import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.shortcuts import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .. import views
from ..models import Advert, Favourite
from ..tests.conftest import (
    TEST_DIR,
)
from ..tokens import account_activation_token


@pytest.mark.django_db
class TestViews:
    """ Class for testing Django Views. """

    pytestmark = pytest.mark.django_db

    def test_upload_data_when_success(self, create_test_csv, client, mocker):
        mocker.patch("parcels.models.Advert.delete_duplicates")

        response = client.post(
            reverse("parcels:upload_data", kwargs={"catalog": TEST_DIR})
        )

        assert response.status_code == 200
        assert Advert.objects.exists()
        Advert.delete_duplicates.assert_called_once()

    def test_upload_data_when_no_files(self, client, mocker):
        mocker.patch("parcels.models.Advert.delete_duplicates")

        response = client.post(
            reverse("parcels:upload_data", kwargs={"catalog": "nonexistent"})
        )

        assert response.status_code == 200
        assert not Advert.objects.exists()
        Advert.delete_duplicates.assert_not_called()

    def test_index(self, client):
        response = client.get(reverse("parcels:index"))
        assert response.status_code == 200

    def test_search_advert_view_get(self, client):
        response = client.get(
            reverse("parcels:search_adverts_form", kwargs={"user_id": 1})
        )
        assert response.status_code == 200

    def test_search_advert_view_post_when_valid(self, factory):
        request = factory.post(
            reverse("parcels:search_adverts_form", kwargs={"user_id": 1}),
            data={"place": "Dębe Wielkie", "price": 200000, "area": 1000},
        )
        response = views.SearchAdvertsView().post(request=request, user_id=1)

        assert response.status_code == 302
        assert "200000" in response.url
        assert "1000" in response.url

    def test_search_advert_view_post_when_invalid(self, factory):
        request = factory.post(
            reverse("parcels:search_adverts_form", kwargs={"user_id": 1}),
            data={"price": 200000, "area": 1000},
        )
        response = views.SearchAdvertsView().post(request=request, user_id=1)

        assert response.status_code == 200

    def test_advert_list_view(
        self, add_testing_data_to_db, test_adverts, add_favourites, user, client
    ):
        kwargs = {
            "place": "Dębe Wielkie",
            "price": 400000,
            "area": 800,
            "user_id": user.id,
        }
        response = client.get(reverse("parcels:advert_list", kwargs=kwargs))
        context = response.context_data
        query = context["object_list"]

        assert list(query.values_list("place")) == [("Dębe Wielkie",)]
        assert list(context["adverts"]) == list(test_adverts)
        for key in ["place", "price", "area"]:
            assert context.get(key) == str(kwargs.get(key))

    def test_advert_detail_view(
        self, add_testing_data_to_db, test_adverts, add_favourites, user, client
    ):
        kwargs = {
            "place": "Dębe Wielkie",
            "price": 400000,
            "area": 800,
        }
        pk = Advert.filter_adverts(**kwargs)[0].id
        kwargs["pk"] = pk
        kwargs["user_id"] = user.id
        response = client.get(reverse("parcels:advert_detail", kwargs=kwargs))
        context = response.context_data
        query = context["object"]

        assert query.place == "Dębe Wielkie"
        assert list(context["adverts"]) == list(test_adverts)
        for key in ["place", "price", "area"]:
            assert context.get(key) == str(kwargs.get(key))

    def test_favourite_list_view(
        self, add_testing_data_to_db, test_adverts, add_favourites, user, client
    ):
        kwargs = {"user_id": user.id}
        response = client.get(reverse("parcels:favourite_list", kwargs=kwargs))
        context = response.context_data
        query = context["object_list"]

        assert list(query.values_list("place")) == [("Dębe Wielkie",), ("Rysie",)]
        assert list(context["adverts"]) == list(test_adverts)

    def test_favourite_detail_view(
        self, add_testing_data_to_db, test_adverts, add_favourites, user, client
    ):
        kwargs = {"pk": test_adverts[0].id, "user_id": user.id}
        response = client.get(reverse("parcels:favourite_detail", kwargs=kwargs))
        context = response.context_data
        query = context["object"]

        assert query.place == "Dębe Wielkie"
        assert list(context["adverts"]) == list(test_adverts)

    def test_register_when_form_valid(self, client):
        valid_data = {
            "username": "test_user",
            "password1": "secret132",
            "password2": "secret132",
            "email1": "test@gmail.com",
            "email2": "test@gmail.com",
        }

        response = client.post("/register", data=valid_data)

        assert response.status_code == 200
        assert User.objects.values("username")[0]["username"] == "test_user"
        assert User.objects.values("email")[0]["email"] == "test@gmail.com"
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Aktywacja konta w aplikacji ParcelsScraper"

    def test_register_when_form_invalid(self, client):
        valid_data = {
            "username": "test_user",
            "password1": "password",
            "password2": "password",
            "email1": "test@gmail.com",
            "email2": "test@gmail.com",
        }

        response = client.post("/register", data=valid_data)

        assert response.status_code == 200
        assert not User.objects.exists()
        assert len(mail.outbox) == 0

    def test_activate(self, client):
        user = User.objects.create(username="test_user", email="test@gmail.com")
        user.set_password("password")
        user.is_active = False
        user.save()

        test_activate_data = {
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        }

        response = client.get(
            reverse("parcels:activate", kwargs=test_activate_data),
            data=test_activate_data,
        )

        assert response.status_code == 302
        assert User.objects.get(pk=user.pk).is_active

    def test_user_login_when_valid(self, client):
        user = User.objects.create(username="test_user", email="test@gmail.com")
        user.set_password("password")
        user.save()

        response = client.post(
            "/user_login", {"username": "test_user", "password": "password"}
        )
        assert response.status_code == 302

    def test_user_login_when_invalid(self, client):
        response = client.post(
            "/user_login", {"username": "test_user", "password": "password"}
        )
        assert response.status_code == 200
        assert str(response.content, encoding="utf8") == "Złe dane logowania!"

    def test_user_logout(self, user, client):
        response = client.post(reverse("parcels:logout"))
        assert response.status_code == 302

    @pytest.mark.parametrize(
        "test_item, reverse_path, assertion",
        [
            (
                {
                    "place": "Dębe Wielkie",
                    "price": 400000,
                    "area": 800,
                    "action": "add",
                    "path_name": "advert_detail",
                },
                "make_favourite",
                [("Dębe Wielkie",)],
            ),
            (
                {
                    "place": "Dębe Wielkie",
                    "price": 400000,
                    "area": 800,
                    "action": "add",
                    "path_name": "advert_list",
                },
                "make_favourite",
                [("Dębe Wielkie",)],
            ),
            (
                {
                    "place": "Rysie",
                    "price": 400000,
                    "area": 800,
                    "action": "add",
                    "path_name": "advert_list",
                },
                "make_all_favourite",
                [("Rysie",)],
            ),
            (
                {
                    "action": "add",
                    "path_name": "favourite_detail",
                },
                "make_favourite_from_favourites",
                [("Dębe Wielkie",)],
            ),
        ],
    )
    def test_handling_favourite_adding(
        self,
        add_testing_data_to_db,
        user,
        factory,
        test_item,
        reverse_path,
        assertion,
    ):
        pk = Advert.objects.get(place="Dębe Wielkie").id
        if reverse_path != "make_all_favourite":
            test_item["pk"] = pk
        test_item["user_id"] = user.id
        request = factory.post(
            reverse("parcels:{}".format(reverse_path), kwargs=test_item)
        )
        request.user = user
        response = views.handling_favourite(request=request, **test_item)

        assert list(Favourite.get_favourites(user.id).values_list("place")) == assertion
        assert response.status_code == 302

    @pytest.mark.parametrize(
        "test_item, reverse_path, assertion",
        [
            (
                {
                    "place": "Dębe Wielkie",
                    "price": 400000,
                    "area": 800,
                    "action": "remove",
                    "path_name": "advert_detail",
                },
                "remove_favourite",
                [("Rysie",)],
            ),
            (
                {
                    "place": "Dębe Wielkie",
                    "price": 400000,
                    "area": 800,
                    "action": "remove",
                    "path_name": "advert_list",
                },
                "remove_favourite",
                [("Rysie",)],
            ),
            (
                {
                    "place": "Rysie",
                    "price": 400000,
                    "area": 800,
                    "action": "remove",
                    "path_name": "advert_list",
                },
                "remove_all_favourite",
                [("Dębe Wielkie",)],
            ),
            (
                {
                    "action": "remove",
                    "path_name": "favourite_detail",
                },
                "remove_favourite_from_favourites",
                [("Rysie",)],
            ),
            (
                {
                    "action": "remove",
                    "path_name": "favourite_list",
                },
                "remove_favourite_from_favourites",
                [("Rysie",)],
            ),
            (
                {
                    "action": "remove_all",
                    "path_name": "favourite_list",
                },
                "remove_all_favourite_from_favourites",
                [],
            ),
        ],
    )
    def test_handling_favourite_removing(
        self,
        add_testing_data_to_db,
        add_favourites,
        user,
        factory,
        test_item,
        reverse_path,
        assertion,
    ):
        pk = Advert.objects.get(place="Dębe Wielkie").id
        if reverse_path not in [
            "remove_all_favourite",
            "remove_all_favourite_from_favourites",
        ]:
            test_item["pk"] = pk
        test_item["user_id"] = user.id
        request = factory.post(
            reverse("parcels:{}".format(reverse_path), kwargs=test_item)
        )
        request.user = user
        response = views.handling_favourite(request=request, **test_item)

        assert list(Favourite.get_favourites(user.id).values_list("place")) == assertion
        assert response.status_code == 302

    def test_streaming_csv(self, add_testing_data_to_db, add_favourites, client):
        response = client.post(reverse("parcels:streaming_csv", kwargs={"user_id": 1}))

        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == '''attachment; filename="your_adverts.csv"'''
        )

    def test_sending_csv(self, add_testing_data_to_db, add_favourites, user, client):
        response = client.post(
            reverse("parcels:sending_csv", kwargs={"user_id": user.id})
        )

        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "ParcelsScraper - wybrane działki"
        assert (
            mail.outbox[0].body
            == "W załączeniu przesyłamy wybrane przez Ciebie działki."
        )
