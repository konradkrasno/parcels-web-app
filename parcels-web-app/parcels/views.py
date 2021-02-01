import csv
import logging
from io import StringIO
from typing import Union

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
    HttpResponse,
    StreamingHttpResponse,
    JsonResponse,
)
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import View, ListView, DetailView

from .forms import AdvertForm, SignUp
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
        else:
            Advert.delete_duplicates()
            return JsonResponse({"OK": "Data successfully updated."})


def register(request: WSGIRequest) -> Union[HttpResponse, render]:
    if request.method == "POST":
        user_form = SignUp(data=request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False
            user.email = user_form.clean_email2()
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
            to_email = user_form.cleaned_data.get("email1")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return HttpResponse("Potwierdź adres email, aby dokończyć rejestrację.")
    user_form = SignUp()
    return render(request, "registration/registration.html", {"user_form": user_form})


def activate(
    request: WSGIRequest, uidb64: str, token: str
) -> Union[HttpResponse, HttpResponseRedirect]:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse("parcels:login"))
    return HttpResponse("Link aktywacyjny jest nieważny.")


def user_login(
    request: WSGIRequest,
) -> Union[HttpResponse, HttpResponseRedirect, render]:
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("parcels:index"))
        else:
            return HttpResponse("Złe dane logowania!")
    else:
        return render(request, "registration/login.html", {})


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
        form = self.form_class(request.POST)
        if form.is_valid():
            context = form.cleaned_data
            return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=context))
        form = AdvertForm()
        return render(request, "parcels/advert_form.html", {"form": form})


class AdvertListView(ListView):
    template_name = "parcels/advert_list.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        place = self.kwargs.get("place")
        price = self.kwargs.get("price")
        area = self.kwargs.get("area")
        queryset = Advert.filter_adverts(place, price, area)
        return queryset

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context["place"] = self.kwargs.get("place")
        context["price"] = self.kwargs.get("price")
        context["area"] = self.kwargs.get("area")
        if self.request.user:
            context["saved_adverts"] = Favourite.get_favourites(
                user_id=self.request.user.id
            )
        return context


class AdvertDetailView(DetailView):
    template_name = "parcels/advert_detail.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        return Advert.get_advert(self.kwargs.get("pk"))

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object", None)
        if queryset is None:
            self.object = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context["place"] = self.kwargs.get("place")
        context["price"] = self.kwargs.get("price")
        context["area"] = self.kwargs.get("area")
        if self.request.user:
            context["saved_adverts"] = Favourite.get_favourites(
                user_id=self.request.user.id
            )
        return context


class FavouriteListView(LoginRequiredMixin, ListView):
    template_name = "parcels/advert_list.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        return Favourite.get_favourites(user_id=self.request.user.id)

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context["place"] = self.kwargs.get("place")
        context["price"] = self.kwargs.get("price")
        context["area"] = self.kwargs.get("area")
        context["saved_adverts"] = Favourite.get_favourites(
            user_id=self.request.user.id
        )
        return context


@login_required
def save_advert(request: WSGIRequest, **kwargs) -> HttpResponseRedirect:
    """ Add advert to favourites adverts. """

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_advert(request: WSGIRequest, **kwargs) -> HttpResponseRedirect:
    """ Delete advert from favourites adverts. """

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def save_all_adverts(request: WSGIRequest, **kwargs) -> HttpResponseRedirect:
    """ Save all adverts from view to favourite adverts. """

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_all_adverts(request: WSGIRequest, **kwargs) -> HttpResponseRedirect:
    """ Delete all adverts from view from favourite adverts. """

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


# @login_required
# def handling_favourite(request, **kwargs) -> HttpResponseRedirect:
#     """ Handling adding or removing adverts from list of favourite. """
#
#     action = kwargs.pop("action")
#     path_name = kwargs.pop("path_name")
#     pk = kwargs.get("pk")
#
#     adverts = Advert.get_advert(pk)
#     if not adverts:
#         if action == "remove_all":
#             adverts = Favourite.get_favourites(user_id=kwargs.get("user_id"))
#         else:
#             try:
#                 adverts = Advert.filter_adverts(
#                     price=kwargs.get("price"),
#                     place=kwargs.get("place"),
#                     area=kwargs.get("area"),
#                 )
#             except ValueError:
#                 pass
#
#     if action == "add":
#         Favourite.add_to_favourite(user_id=kwargs.get("user_id"), adverts=adverts)
#     elif action in ["remove", "remove_all"]:
#         Favourite.remove_from_favourite(user_id=kwargs.get("user_id"), adverts=adverts)
#
#     if path_name in ["advert_list", "favourite_list"]:
#         try:
#             kwargs.pop("pk")
#         except KeyError:
#             pass
#
#     return HttpResponseRedirect(reverse("parcels:{}".format(path_name), kwargs=kwargs))


class Echo:
    """ Helper class for streaming csv file. """

    @staticmethod
    def write(value):
        return value


def streaming_csv(request: WSGIRequest, user_id: int) -> StreamingHttpResponse:
    adverts = Favourite.get_favourites(user_id=user_id)
    rows = [
        [
            "Miejscowość",
            "Powiat",
            "Cena",
            "Cena za m2",
            "Powierzchnia",
            "Link",
            "Data dodania",
        ]
    ]
    for adv in adverts:
        row = [
            adv.place,
            adv.county,
            adv.price,
            adv.price_per_m2,
            adv.area,
            adv.link,
            adv.date_added,
        ]
        rows.append(row)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows), content_type="text/csv"
    )
    response["Content-Disposition"] = 'attachment; filename="your_adverts.csv"'
    return response


def sending_csv(request: WSGIRequest, user_id: int) -> HttpResponseRedirect:
    adverts = Favourite.get_favourites(user_id=user_id)
    rows = [
        [
            "Miejscowość",
            "Powiat",
            "Cena",
            "Cena za m2",
            "Powierzchnia",
            "Link",
            "Data dodania",
        ]
    ]
    for adv in adverts:
        row = [
            adv.place,
            adv.county,
            adv.price,
            adv.price_per_m2,
            adv.area,
            adv.link,
            adv.date_added,
        ]
        rows.append(row)
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    [writer.writerow(row) for row in rows]
    user = User.objects.get(pk=user_id)
    to_email = user.email
    email = EmailMessage(
        "ParcelsScraper - wybrane działki",
        "W załączeniu przesyłamy wybrane przez Ciebie działki.",
        to=[to_email],
    )
    email.attach("your_adverts.csv", csv_file.getvalue(), "text/csv")
    email.send()
    context = {"user_id": user_id}
    return HttpResponseRedirect(reverse("parcels:favourite_list", kwargs=context))
