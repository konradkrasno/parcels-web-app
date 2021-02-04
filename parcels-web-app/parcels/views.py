import csv
import json
import logging
from io import StringIO
from typing import *

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.db.utils import ProgrammingError
from django.http import (
    HttpResponseRedirect,
    StreamingHttpResponse,
    JsonResponse,
)
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import View, ListView, DetailView

from .forms import AdvertForm, SignUpForm, LoginForm
from .helpers import prepare_csv, Echo
from .models import Advert, Favourite
from .tokens import account_activation_token

logging.basicConfig(level=logging.DEBUG)


class UploadData(View):
    """ Uploading data from json file to database. """

    @staticmethod
    def post(request: WSGIRequest, catalog: str) -> JsonResponse:
        try:
            Advert.load_adverts(catalog)
        except (ProgrammingError, FileNotFoundError) as e:
            logging.error(e.__str__())
            return JsonResponse({"OK": e.__str__()})
        Advert.delete_duplicates()
        return JsonResponse({"OK": "Data successfully updated."})


def register(request: WSGIRequest) -> Union[HttpResponseRedirect, render]:
    if request.method == "POST":
        form = SignUpForm(data=request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.email = form.clean_email2()
            user.save()
            current_site = get_current_site(request)
            mail_subject = "Aktywacja konta w aplikacji ParcelsScraper"
            message = render_to_string(
                "registration/active_mail.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                },
            )
            to_email = form.cleaned_data.get("email1")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            messages.success(
                request, "Potwierdź adres email, aby dokończyć rejestrację."
            )
            return HttpResponseRedirect(reverse("parcels:login"))
        else:
            for errors in json.loads(form.errors.as_json()).values():
                for error in errors:
                    messages.error(request, error["message"])
    form = SignUpForm()
    return render(request, "registration/registration.html", {"form": form})


def activate(request: WSGIRequest, uidb64: str, token: str) -> HttpResponseRedirect:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse("parcels:login"))
    messages.info(request, "Link aktywacyjny jest nieważny.")
    return HttpResponseRedirect(reverse("parcels:register"))


def user_login(
    request: WSGIRequest,
) -> Union[HttpResponseRedirect, render]:
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                return HttpResponseRedirect(reverse("parcels:index"))
            messages.error(request, "Złe dane logowania!")
            return HttpResponseRedirect(reverse("parcels:login"))
        else:
            for errors in json.loads(form.errors.as_json()).values():
                for error in errors:
                    messages.error(request, error["message"])
    form = LoginForm()
    return render(request, "registration/login.html", {"form": form})


@login_required
def user_logout(request: WSGIRequest) -> HttpResponseRedirect:
    logout(request)
    return HttpResponseRedirect(reverse("parcels:index"))


class Index(View):
    template_name = "parcels/advert_form.html"
    form_class = AdvertForm

    def get(self, request: WSGIRequest) -> render:
        form = self.form_class()
        return render(request, "parcels/advert_form.html", {"form": form})

    def post(self, request: WSGIRequest) -> Union[HttpResponseRedirect, render]:
        form = self.form_class(self.request.POST)
        if form.is_valid():
            if self.request.user.is_authenticated:
                self.request.session.update(form.cleaned_data)
            return HttpResponseRedirect(
                "{}?place={place}&price={price}&area={area}".format(
                    reverse('parcels:advert_list'),
                    **form.cleaned_data,
                )
            )
        else:
            for errors in json.loads(form.errors.as_json()).values():
                for error in errors:
                    messages.error(request, error["message"])
        form = AdvertForm()
        return render(self.request, "parcels/advert_form.html", {"form": form})


class AdvertListView(ListView):
    template_name = "parcels/advert_list.html"
    paginate_by = 15
    model = Advert

    def get_queryset(self) -> QuerySet:
        if self.request.user.is_authenticated:
            place = self.request.session.get("place", "None")
            price = self.request.session.get("price", 0)
            area = self.request.session.get("area", 0)
        else:
            place = self.request.GET.get("place", "None")
            price = self.request.GET.get("price", 0)
            area = self.request.GET.get("area", 0)
        queryset = Advert.filter_adverts(place, price, area)
        return queryset

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        self.request.session["view_name"] = "adverts"
        return context


class FavouriteListView(LoginRequiredMixin, ListView):
    template_name = "parcels/advert_list.html"
    paginate_by = 15
    model = Advert

    def get_queryset(self) -> QuerySet:
        return Favourite.get_favourites(user_id=self.request.user.id)

    @staticmethod
    def get_next_url(context: Dict) -> str:
        page_obj = context.get("page_obj")
        if len(page_obj.object_list) < 2 and page_obj.has_previous():
            next_page = page_obj.previous_page_number()
        else:
            next_page = page_obj.number
        return f"{reverse('parcels:favourite_list')}?page={next_page}"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        self.request.session["next_url"] = self.get_next_url(context)
        self.request.session["view_name"] = "favourites"
        return context


class AdvertDetailView(DetailView):
    template_name = "parcels/advert_detail.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        return Advert.get_advert(self.kwargs.get("pk"))

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        return context


@login_required
def save_advert(request: WSGIRequest, pk: int) -> HttpResponseRedirect:
    """ Add advert to favourites adverts. """

    advert = Advert.get_advert(_id=pk)
    Favourite.add_to_favourite(user_id=request.user.id, adverts=advert)
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_advert(request: WSGIRequest, pk: int) -> HttpResponseRedirect:
    """ Delete advert from favourites adverts. """

    advert = Advert.get_advert(_id=pk)
    Favourite.remove_from_favourite(user_id=request.user.id, adverts=advert)
    next_url = request.session.get("next_url", None)
    view_name = request.session.get("view_name")
    if next_url is None or view_name == 'adverts':
        next_url = request.META["HTTP_REFERER"]
    return HttpResponseRedirect(next_url)


@login_required
def save_all_adverts(request: WSGIRequest) -> HttpResponseRedirect:
    """ Save all adverts from view to favourite adverts. """

    adverts = Advert.filter_adverts(
        place=request.session.get("place"),
        price=request.session.get("price"),
        area=request.session.get("area"),
    )
    Favourite.add_to_favourite(user_id=request.user.id, adverts=adverts)
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_all_adverts(request: WSGIRequest) -> HttpResponseRedirect:
    """ Delete all adverts from view from favourite adverts. """

    if request.session.get("view_name") == "favourites":
        adverts = request.saved_adverts
        next_url = reverse("parcels:favourite_list")
    else:
        adverts = Advert.filter_adverts(
            place=request.session.get("place"),
            price=request.session.get("price"),
            area=request.session.get("area"),
        )
        next_url = request.META["HTTP_REFERER"]
    Favourite.remove_from_favourite(user_id=request.user.id, adverts=adverts)
    return HttpResponseRedirect(next_url)


def streaming_csv(request: WSGIRequest) -> StreamingHttpResponse:
    adverts = Favourite.get_favourites(user_id=request.user.id)
    rows = prepare_csv(adverts)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows), content_type="text/csv"
    )
    response["Content-Disposition"] = 'attachment; filename="your_adverts.csv"'
    return response


def sending_csv(request: WSGIRequest) -> HttpResponseRedirect:
    adverts = Favourite.get_favourites(user_id=request.user.id)
    rows = prepare_csv(adverts)
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    [writer.writerow(row) for row in rows]
    user = User.objects.get(pk=request.user.id)
    to_email = user.email
    email = EmailMessage(
        "ParcelsScraper - wybrane działki",
        "W załączeniu przesyłamy wybrane przez Ciebie działki.",
        to=[to_email],
    )
    email.attach("your_adverts.csv", csv_file.getvalue(), "text/csv")
    email.send()
    return HttpResponseRedirect(request.META["HTTP_REFERER"])
