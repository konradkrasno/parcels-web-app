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
from django.db.models import QuerySet
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
from django.views.generic.edit import FormMixin

from . import tasks
from .forms import AdvertForm, SignUpForm, LoginForm, SearchForm
from .helpers import prepare_csv, Echo, get_adverts
from .models import Advert, Favourite
from .tasks import send_email
from .tokens import account_activation_token

logging.basicConfig(level=logging.DEBUG)


def error_404(request, exception):
    return render(request, "errors/404.html", locals())


def error_500(request, exception=None):
    return render(request, "errors/500.html", locals())


def run_spider(request: WSGIRequest) -> JsonResponse:
    tasks.run_spider.delay()
    return JsonResponse({"OK": "Spider run task pushed"})


def upload_data(request: WSGIRequest) -> JsonResponse:
    tasks.upload_data.delay()
    return JsonResponse({"OK": "Uploading data task pushed."})


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
            recipient = form.cleaned_data.get("email1")
            send_email.delay(subject=mail_subject, body=message, to=[recipient])
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
        form = self.form_class(data_list=Advert.get_places())
        return render(request, "parcels/advert_form.html", {"form": form})

    def post(self, request: WSGIRequest) -> Union[HttpResponseRedirect, render]:
        form = self.form_class(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(
                "{}?place={place}&price={price}&area={area}".format(
                    reverse("parcels:advert_list"),
                    **form.cleaned_data,
                )
            )
        else:
            for errors in json.loads(form.errors.as_json()).values():
                for error in errors:
                    messages.error(request, error["message"])
        form = self.form_class()
        return render(self.request, "parcels/advert_form.html", {"form": form})


class AdvertListView(FormMixin, ListView):
    template_name = "parcels/advert_list.html"
    paginate_by = 15
    model = Advert
    form_class = SearchForm

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        place = self.request.GET.get("place", None)
        price = self.request.GET.get("price", 0)
        area = self.request.GET.get("area", 0)
        search_text = self.request.GET.get("search_text", None)
        queryset = Advert.filter_adverts(place, price, area, search_text)
        return queryset

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        self.request.session["view_name"] = "adverts"
        return context

    def post(self, request, *args, **kwargs):
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        form = self.form_class(request.POST)
        context["search_text"] = None
        if form.is_valid():
            context["search_text"] = form.cleaned_data.get("search_text", None)
        self.request.session["view_name"] = "adverts"
        return HttpResponseRedirect(
            "{}?place={place}&price={price}&area={area}&search_text={search_text}".format(
                reverse("parcels:advert_list"), **context
            )
        )


class FavouriteListView(LoginRequiredMixin, FormMixin, ListView):
    template_name = "parcels/advert_list.html"
    paginate_by = 15
    model = Advert
    form_class = SearchForm

    def get_queryset(self) -> QuerySet:
        search_text = self.request.GET.get("search_text", None)
        queryset = Favourite.get_favourites(
            user_id=self.request.user.id, search_text=search_text
        )
        return queryset

    @staticmethod
    def get_next_url(context: Dict) -> str:
        page_obj = context.get("page_obj", 1)
        search_text = context.get("search_text", None)
        if len(page_obj.object_list) < 2 and page_obj.has_previous():
            next_page = page_obj.previous_page_number()
        else:
            next_page = page_obj.number
        return f"{reverse('parcels:favourite_list')}?search_text={search_text}&page={next_page}"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        self.request.session["next_url"] = self.get_next_url(context)
        self.request.session["view_name"] = "favourites"
        return context

    def post(self, request, *args, **kwargs):
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET.dict())
        form = self.form_class(request.POST)
        context["search_text"] = None
        if form.is_valid():
            context["search_text"] = form.cleaned_data.get("search_text", None)
        self.request.session["view_name"] = "favourites"
        return HttpResponseRedirect(
            "{}?search_text={search_text}".format(
                reverse("parcels:favourite_list"), **context
            )
        )


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
    view_name = request.session.get("view_name", None)
    if next_url is None or view_name != "favourites":
        next_url = request.META["HTTP_REFERER"]
    return HttpResponseRedirect(next_url)


@login_required
def save_all_adverts(request: WSGIRequest) -> HttpResponseRedirect:
    """ Save all adverts from view to favourite adverts. """

    adverts = Advert.filter_adverts(
        place=request.GET.get("place", None),
        price=request.GET.get("price", 0),
        area=request.GET.get("area", 0),
        search_text=request.GET.get("search_text", None),
    )
    Favourite.add_to_favourite(user_id=request.user.id, adverts=adverts)
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_all_adverts(request: WSGIRequest) -> HttpResponseRedirect:
    """ Delete all adverts from view from favourite adverts. """

    if request.session.get("view_name", None) == "favourites":
        next_url = reverse("parcels:favourite_list")
    else:
        next_url = request.META["HTTP_REFERER"]
    adverts = get_adverts(request)
    Favourite.remove_from_favourite(user_id=request.user.id, adverts=adverts)
    return HttpResponseRedirect(next_url)


def streaming_csv(request: WSGIRequest) -> StreamingHttpResponse:
    adverts = get_adverts(request)
    rows = prepare_csv(adverts)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows), content_type="text/csv"
    )
    response["Content-Disposition"] = 'attachment; filename="your_adverts.csv"'
    return response


def sending_csv(request: WSGIRequest) -> HttpResponseRedirect:
    adverts = get_adverts(request)
    rows = prepare_csv(adverts)
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    [writer.writerow(row) for row in rows]
    user = User.objects.get(pk=request.user.id)
    recipient = user.email
    send_email.delay(
        subject="ParcelsScraper - wybrane działki",
        body="W załączeniu przesyłamy wybrane przez Ciebie działki.",
        to=[recipient],
        attachments=[("your_adverts.csv", csv_file.getvalue(), "text/csv")],
    )
    return HttpResponseRedirect(request.META["HTTP_REFERER"])
