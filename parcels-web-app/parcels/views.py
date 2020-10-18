import logging

from django.shortcuts import render, reverse
from django.contrib.sites.shortcuts import get_current_site

from django.template.loader import render_to_string

from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    StreamingHttpResponse,
    JsonResponse,
)

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import View, TemplateView, ListView, DetailView
from parcels.models import Advert, Favourite
from parcels.forms import AdvertForm, SignUp

from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from parcels.tokens import account_activation_token

from django.db.utils import ProgrammingError
from django.db.models import QuerySet

import csv
from io import StringIO

logging.basicConfig(level=logging.DEBUG)


class UploadData(View):
    """ Uploading data from json file to database. """

    @staticmethod
    def post(request) -> JsonResponse:
        try:
            Advert.load_adverts("scraped_data")

        except (ProgrammingError, FileNotFoundError) as e:
            logging.error(e.__str__())
            return JsonResponse({"OK": e.__str__()})

        else:
            Advert.delete_duplicates()
            return JsonResponse({"OK": "Data successfully updated."})


class Index(TemplateView):
    template_name = "parcels/index.html"


class SearchAdvertsView(View):
    template_name = "parcels/advert_form.html"
    form_class = AdvertForm

    def get(self, request, user_id: int) -> render:
        form = self.form_class()
        return render(request, "parcels/advert_form.html", {"form": form})

    def post(self, request, user_id: int):
        form = self.form_class(request.POST)

        if form.is_valid():
            context = form.cleaned_data
            context["user_id"] = user_id
            return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=context))

        else:
            form = AdvertForm()
        return render(request, "parcels/advert_form.html", {"form": form})


class AdvertListView(ListView):
    template_name = "parcels/advert_list.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(
            place=self.kwargs.get("place"),
            price__lte=self.kwargs.get("price"),
            area__gte=self.kwargs.get("area"),
        ).order_by("price")

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()

        context = super().get_context_data(**kwargs)
        context["place"] = self.kwargs.get("place")
        context["price"] = self.kwargs.get("price")
        context["area"] = self.kwargs.get("area")

        if self.kwargs.get("user_id"):
            favourite = Favourite()
            fav_id = favourite.get_favourite_ids(user_id=self.kwargs.get("user_id"))
            context["fav_id"] = fav_id

        return context


class AdvertDetailView(DetailView):
    template_name = "parcels/advert_detail.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object", None)
        if queryset is None:
            self.object = self.get_queryset()

        context = super().get_context_data(**kwargs)
        context["place"] = self.kwargs.get("place")
        context["price"] = self.kwargs.get("price")
        context["area"] = self.kwargs.get("area")

        if self.kwargs.get("user_id"):
            favourite = Favourite()
            fav_id = favourite.get_favourite_ids(user_id=self.kwargs.get("user_id"))
            context["fav_id"] = fav_id

        return context


class FavouriteListView(LoginRequiredMixin, ListView):
    template_name = "parcels/favourite_list.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        fav_id = Favourite.get_favourite_ids(user_id=self.kwargs.get("user_id"))
        return queryset.filter(pk__in=fav_id).order_by("place")

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()

        favourite = Favourite()
        fav_id = favourite.get_favourite_ids(user_id=self.kwargs.get("user_id"))

        context = super().get_context_data(**kwargs)
        context["fav_id"] = fav_id

        return context


class FavouriteDetailView(LoginRequiredMixin, DetailView):
    template_name = "parcels/favourite_detail.html"
    model = Advert

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs) -> dict:
        queryset = kwargs.pop("object", None)
        if queryset is None:
            self.object = self.get_queryset()

        favourite = Favourite()
        fav_id = favourite.get_favourite_ids(user_id=self.kwargs.get("user_id"))

        context = super().get_context_data(**kwargs)
        context["fav_id"] = fav_id

        return context


def register(request):
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
            return HttpResponse("Potwierź adres email, aby dokończyć rejestrację.")

    else:
        user_form = SignUp()

    return render(
        request,
        "registration/registration.html",
        {
            "user_form": user_form,
        },
    )


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        return HttpResponseRedirect(reverse("parcels:login"))
    return HttpResponse("Link aktywacyjny jest nieważny.")


def user_login(request):
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
def user_logout(request) -> HttpResponseRedirect:
    logout(request)
    return HttpResponseRedirect(reverse("parcels:index"))


@login_required
def make_favourite(request, **kwargs) -> HttpResponseRedirect:
    """ Adding advert to list of favourite in advert_detail view. """

    print("request:", request)

    favourite = Favourite()
    favourite.create_or_update(pk=kwargs.get("pk"), user_id=kwargs.get("user_id"))

    return HttpResponseRedirect(reverse("parcels:advert_detail", kwargs=kwargs))


@login_required
def make_favourite_list(request, **kwargs) -> HttpResponseRedirect:
    """ Adding advert to list of favourite in advert_list view. """

    favourite = Favourite()
    favourite.create_or_update(pk=kwargs.get("pk"), user_id=kwargs.get("user_id"))

    kwargs.pop("pk")

    return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=kwargs))


@login_required
def make_all_favourite(request, **kwargs) -> HttpResponseRedirect:
    """ Adding all adverts to list of favourite in advert_list view. """

    filtered_adverts = Advert.filter_adverts(
        price=kwargs.get("price"), place=kwargs.get("place"), area=kwargs.get("area")
    )

    favourite = Favourite()
    favourite.make_many_favourite(
        user_id=kwargs.get("user_id"), adverts=filtered_adverts
    )

    return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=kwargs))


@login_required
def make_favourite_from_favourites(request, **kwargs) -> HttpResponseRedirect:
    """ Adding advert to list of favourite in favourite_detail view. """

    favourite = Favourite()
    favourite.create_or_update(pk=kwargs.get("pk"), user_id=kwargs.get("user_id"))

    return HttpResponseRedirect(reverse("parcels:favourite_detail", kwargs=kwargs))


@login_required
def remove_favourite(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting advert from list of favourite in advert_detail view. """

    favourite = Favourite()
    favourite.remove_from_favourite(pk=kwargs.get("pk"), user_id=kwargs.get("user_id"))

    return HttpResponseRedirect(reverse("parcels:advert_detail", kwargs=kwargs))


@login_required
def remove_favourite_list(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting advert from list of favourite in advert_list view. """

    favourite = Favourite()
    favourite.remove_from_favourite(pk=kwargs.get("pk"), user_id=kwargs.get("user_id"))

    kwargs.pop("pk")

    return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=kwargs))


@login_required
def remove_all_favourite(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting all adverts from list of favourite in advert_list view. """

    filtered_adverts = Advert.filter_adverts(
        price=kwargs.get("price"), place=kwargs.get("place"), area=kwargs.get("area")
    )

    favourite = Favourite()
    favourite.remove_from_favourite(
        user_id=kwargs.get("user_id"), adverts=filtered_adverts
    )

    return HttpResponseRedirect(reverse("parcels:advert_list", kwargs=kwargs))


@login_required
def remove_favourite_from_favourites(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting advert from list of favourite in favourite_detail view. """

    favourite = Favourite()
    favourite.remove_from_favourite(**kwargs)

    return HttpResponseRedirect(reverse("parcels:favourite_detail", kwargs=kwargs))


@login_required
def remove_favourite_from_favourites_list(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting advert from list of favourite in favourite_list view. """

    favourite = Favourite()
    favourite.remove_from_favourite(**kwargs)

    kwargs.pop("pk")

    return HttpResponseRedirect(reverse("parcels:favourite_list", kwargs=kwargs))


@login_required
def remove_all_favourite_from_favourites(request, **kwargs) -> HttpResponseRedirect:
    """ Deleting all adverts from list of favourite in favourite_list view. """

    favourite = Favourite()
    fav_id = favourite.get_favourite_ids(user_id=kwargs.get("user_id"))
    favourite.remove_from_favourite(user_id=kwargs.get("user_id"), adverts=fav_id)

    return HttpResponseRedirect(reverse("parcels:favourite_list", kwargs=kwargs))


class Echo:
    """ Helper class for streaming csv file. """

    @staticmethod
    def write(value):
        return value


def streaming_csv_view(request, user_id: int) -> StreamingHttpResponse:
    favourite = Favourite()
    fav_id = favourite.get_favourite_ids(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by("place")

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
    for adv in favourite_list:
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


def sending_csv_view(request, user_id: int) -> HttpResponseRedirect:
    favourite = Favourite()
    fav_id = favourite.get_favourite_ids(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by("place")

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
    for adv in favourite_list:
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
