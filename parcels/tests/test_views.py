import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from parcels import tasks
from parcels import views
from parcels.models import Advert, Favourite
from parcels.tokens import account_activation_token


@pytest.mark.django_db
class TestViews:
    """ Class for testing Django Views. """

    pytestmark = pytest.mark.django_db

    def test_run_spider(self, client, mocker):
        mocker.patch("parcels.tasks.run_spider.delay")
        response = client.get(reverse("parcels:run_spider"))
        assert response.status_code == 200
        tasks.run_spider.delay.assert_called_once()

    def test_upload_data(self, client, mocker):
        mocker.patch("parcels.tasks.upload_data.delay")
        response = client.get(reverse("parcels:upload_data"))
        assert response.status_code == 200
        tasks.upload_data.delay.assert_called_once()

    def test_index_get(self, client):
        response = client.get(reverse("parcels:index"))
        assert response.status_code == 200

    def test_index_post(self, factory):
        request = factory.post(reverse("parcels:index"), data={})
        request.user = AnonymousUser()
        response = views.Index().post(request=request)
        assert response.status_code == 302
        assert "?place=None&price=0&area=0" in response.url

    def test_advert_list_view(self, client):
        kwargs = {
            "place": "Dębe Wielkie",
            "price": 400000,
            "area": 800,
        }
        response = client.get(reverse("parcels:advert_list"), kwargs)
        context = response.context_data
        query = context["object_list"]
        assert list(query.values_list("place")) == [("Dębe Wielkie",)]
        for key in ["place", "price", "area"]:
            assert context.get(key) == str(kwargs.get(key))

    def test_advert_list_view_post(self, client, mocker):
        kwargs = {
            "place": None,
            "price": 0,
            "area": 0,
        }
        response = client.post(
            "{}?place={place}&price={price}&area={area}".format(
                reverse("parcels:advert_list"),
                **kwargs,
            )
        )
        assert response.status_code == 302
        assert "?place=None&price=0&area=0&search_text=None" in response.url

    def test_advert_detail_view(self, client):
        kwargs = {
            "place": "Dębe Wielkie",
            "price": 400000,
            "area": 800,
        }
        pk = Advert.filter_adverts(**kwargs)[0].id
        response = client.get(
            reverse("parcels:advert_detail", kwargs={"pk": pk}), kwargs
        )
        context = response.context_data
        query = context["object"]

        assert query.place == "Dębe Wielkie"
        for key in ["place", "price", "area"]:
            assert context.get(key) == str(kwargs.get(key))

    def test_favourite_list_view(self, test_adverts, add_favourites, user, client):
        response = client.get(reverse("parcels:favourite_list"))
        context = response.context_data
        query = context["object_list"]
        assert len(query.values_list("place")) == 3

    def test_favourite_list_view_post(self, user, client):
        response = client.post(reverse("parcels:favourite_list"))
        assert response.status_code == 302
        assert "?search_text=None" in response.url

    def test_register_when_valid_form(self, client, mocker):
        mocker.patch("parcels.tasks.send_email.delay")
        valid_data = {
            "username": "test_user",
            "password1": "secret132",
            "password2": "secret132",
            "email1": "test@gmail.com",
            "email2": "test@gmail.com",
        }

        response = client.post("/register", data=valid_data)

        assert response.status_code == 302
        assert User.objects.values("username")[0]["username"] == "test_user"
        assert User.objects.values("email")[0]["email"] == "test@gmail.com"
        tasks.send_email.delay.assert_called_once()

    def test_register_when_invalid_form(self, client, mocker):
        mocker.patch("parcels.tasks.send_email.delay")
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
        tasks.send_email.delay.assert_not_called()

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
        assert response.status_code == 302

    def test_user_logout(self, user, client):
        response = client.post(reverse("parcels:logout"))
        assert response.status_code == 302

    def test_save_advert(self, user, client):
        pk = Advert.objects.get(place="Dębe Wielkie").id
        response = client.post(
            reverse("parcels:save_advert", kwargs={"pk": pk}),
            HTTP_REFERER="http://foo/bar",
        )
        assert response.status_code == 302
        assert list(Favourite.get_favourites(user.id).values_list("place")) == [
            ("Dębe Wielkie",)
        ]

    def test_delete_advert(self, user, client, add_favourites):
        pk = Advert.objects.get(place="Dębe Wielkie").id
        response = client.post(
            reverse("parcels:delete_advert", kwargs={"pk": pk}),
            HTTP_REFERER="http://foo/bar",
        )
        assert response.status_code == 302
        assert list(Favourite.get_favourites(user.id).values_list("place")) == [
            ("Rysie",),
            ("Rysie",),
        ]

    def test_save_all_adverts(self, user, client):
        response = client.post(
            reverse("parcels:save_all_adverts"), HTTP_REFERER="http://foo/bar"
        )
        assert response.status_code == 302
        assert len(Favourite.get_favourites(user.id).values_list("place")) == 3

    def test_delete_all_adverts(self, user, client, add_favourites):
        response = client.post(
            reverse("parcels:delete_all_adverts"), HTTP_REFERER="http://foo/bar"
        )
        assert response.status_code == 302
        assert list(Favourite.get_favourites(user.id).values_list("place")) == []

    def test_streaming_csv(self, add_favourites, client):
        response = client.post(reverse("parcels:download_csv"))

        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == '''attachment; filename="your_adverts.csv"'''
        )

    def test_sending_csv(self, add_favourites, user, client, mocker):
        mocker.patch("parcels.tasks.send_email.delay")
        response = client.post(
            reverse("parcels:send_csv"), HTTP_REFERER="http://foo/bar"
        )

        assert response.status_code == 302
        tasks.send_email.delay.assert_called_once()
