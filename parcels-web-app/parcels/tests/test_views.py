import pytest

from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from parcels import views
from parcels.tests.fixtures import (
    create_test_csv,
    add_testing_data_to_db,
    add_favourite,
    client,
    logged_client,
    factory,
    TEST_DIR,
)
from parcels.models import Advert
from parcels.tokens import account_activation_token


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

    @pytest.mark.parametrize(
        "path, kwargs, object_type, assertion, additional_context_key",
        [
            (
                "advert_list",
                {"place": "Dębe Wielkie", "price": 400000, "area": 800, "user_id": 1},
                "object_list",
                ["Dębe Wielkie"],
                ["place", "price", "area"],
            ),
            (
                "advert_detail",
                {
                    "place": "Dębe Wielkie",
                    "price": 400000,
                    "area": 800,
                    "pk": 1,
                    "user_id": 1,
                },
                "object",
                "Dębe Wielkie",
                ["place", "price", "area"],
            ),
            (
                "favourite_list",
                {"user_id": 1},
                "object_list",
                ["Dębe Wielkie", "Rysie"],
                [],
            ),
            ("favourite_detail", {"pk": 1, "user_id": 1}, "object", "Dębe Wielkie", []),
        ],
    )
    def tests_advert_and_favourite_views(
        self,
        add_testing_data_to_db,
        add_favourite,
        logged_client,
        path,
        kwargs,
        object_type,
        assertion,
        additional_context_key,
    ):
        response = logged_client.get(reverse("parcels:{}".format(path), kwargs=kwargs))
        context = response.context_data
        query = context[object_type]

        try:
            result = [value["place"] for value in query.values("place")]
        except AttributeError:
            result = query.place

        assert result == assertion
        assert context["fav_id"] == [1, 2]

        for key in additional_context_key:
            assert context.get(key) == str(kwargs.get(key))

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

        response = client.get(reverse("parcels:activate", kwargs=test_activate_data), data=test_activate_data)

        assert response.status_code == 302
        assert User.objects.get(pk=user.pk).is_active

    def test_user_login_when_valid(self, client):
        user = User.objects.create(username="test_user", email="test@gmail.com")
        user.set_password("password")
        user.save()

        response = client.post("/user_login", {"username": "test_user", "password": "password"})
        assert response.status_code == 302

    def test_user_login_when_invalid(self, client):
        response = client.post("/user_login", {"username": "test_user", "password": "password"})
        assert response.status_code == 200
        assert str(response.content, encoding='utf8') == "Złe dane logowania!"

    def test_user_logout(self, logged_client):
        assert logged_client.login
        response = logged_client.post(reverse("parcels:logout"))
        assert response.status_code == 302

    def test_make_favourite(self):
        pass

    def test_make_favourite_list(self):
        pass

    def test_make_all_favourite(self):
        pass

    def test_make_favourite_from_favourites(self):
        pass

    def test_remove_favourite(self):
        pass

    def test_remove_favourite_list(self):
        pass

    def test_remove_all_favourite(self):
        pass

    def test_remove_favourite_from_favourites(self):
        pass

    def test_remove_favourite_from_favourites_list(self):
        pass

    def remove_all_favourite_from_favourites(self):
        pass

#######
    def test_streaming_csv(self):
        pass

    def test_sending_csv(self):
        pass


#
#
#
# class MakeFavouriteTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#
#         self.user = User.objects.create(username="test_user", email="test@gmail.com")
#         self.user.set_password("password")
#         self.user.save()
#         self.client.login(username="test_user", password="password")
#
#         Advert.objects.all().delete()
#         for item in data:
#             advert = Advert(**item)
#             advert.save()
#
#     def test_make_favourite(self):
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "pk": 100,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(reverse("parcels:make_favourite", kwargs=test_data))
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "100")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("100", response.url)
#         self.assertIn("1", response.url)
#
#     def test_make_favourite_list(self):
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "pk": 100,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(
#             reverse("parcels:make_favourite_list", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "100")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("1", response.url)
#
#     def test_make_all_favourite(self):
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(
#             reverse("parcels:make_all_favourite", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "1,3,4")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("1", response.url)
#
#     def test_make_favourite_from_favourites(self):
#         test_data = {"pk": 100, "user_id": self.user.id}
#
#         response = self.client.post(
#             reverse("parcels:make_favourite_from_favourites", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "100")
#         self.assertIn("100", response.url)
#         self.assertIn("1", response.url)
#
#     def test_remove_favourite(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=100, user_id=1)
#         favourite.add_to_favourite(pk=101)
#         favourite.save()
#
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "pk": 100,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(
#             reverse("parcels:remove_favourite", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "101")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("100", response.url)
#         self.assertIn("1", response.url)
#
#     def test_remove_favourite_list(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=100, user_id=1)
#         favourite.add_to_favourite(pk=101)
#         favourite.save()
#
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "pk": 100,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(
#             reverse("parcels:remove_favourite_list", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "101")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("1", response.url)
#
#     def test_remove_all_favourite(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=1, user_id=1)
#         favourite.add_to_favourite(pk=2)
#         favourite.add_to_favourite(pk=3)
#         favourite.add_to_favourite(pk=4)
#         favourite.add_to_favourite(pk=5)
#         favourite.save()
#
#         test_data = {
#             "place": "Dębe Wielkie",
#             "price": 400000,
#             "area": 1000,
#             "user_id": self.user.id,
#         }
#
#         response = self.client.post(
#             reverse("parcels:remove_all_favourite", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "2,5")
#         self.assertIn("400000", response.url)
#         self.assertIn("1000", response.url)
#         self.assertIn("1", response.url)
#
#     def test_remove_favourite_from_favourites(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=100, user_id=1)
#         favourite.add_to_favourite(pk=101)
#         favourite.save()
#
#         test_data = {"pk": 100, "user_id": self.user.id}
#
#         response = self.client.post(
#             reverse("parcels:remove_favourite_from_favourites", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "101")
#         self.assertIn("100", response.url)
#         self.assertIn("1", response.url)
#
#     def test_remove_favourite_from_favourites_list(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=100, user_id=1)
#         favourite.add_to_favourite(pk=101)
#         favourite.save()
#
#         test_data = {"pk": 100, "user_id": self.user.id}
#
#         response = self.client.post(
#             reverse("parcels:remove_favourite_from_favourites_list", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "101")
#         self.assertIn("1", response.url)
#
#     def test_remove_all_favourite_from_favourites(self):
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=100, user_id=1)
#         favourite.add_to_favourite(pk=101)
#         favourite.add_to_favourite(pk=102)
#         favourite.add_to_favourite(pk=103)
#         favourite.add_to_favourite(pk=104)
#         favourite.save()
#
#         test_data = {"user_id": self.user.id}
#
#         response = self.client.post(
#             reverse("parcels:remove_all_favourite_from_favourites", kwargs=test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], "")
#         self.assertIn("1", response.url)
#
#
# class CSVTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.factory = RequestFactory()
#
#         self.user = User.objects.create(username="test_user", email="test@gmail.com")
#         self.user.set_password("password")
#         self.user.save()
#         self.client.login(username="test_user", password="password")
#
#         self.test_data = {"user_id": self.user.id}
#
#         Advert.objects.all().delete()
#         for item in data:
#             advert = Advert(**item)
#             advert.save()
#
#         favourite = Favourite()
#         favourite.add_to_favourite_first_time(pk=1, user_id=1)
#         favourite.add_to_favourite(pk=2)
#         favourite.add_to_favourite(pk=3)
#         favourite.add_to_favourite(pk=5)
#         favourite.save()
#
#     def test_streaming_csv_view(self):
#         response = self.client.post(
#             reverse("parcels:streaming_csv", kwargs=self.test_data)
#         )
#
#         response_data = []
#         for row in response:
#             response_data.append(str(row, encoding="utf-8"))
#
#         self.assertEqual(response.status_code, 200)
#         self.assertEquals(
#             response.get("Content-Disposition"),
#             '''attachment; filename="your_adverts.csv"''',
#         )
#         self.assertIn((data[0]["place"]), response_data[1])
#         self.assertIn((data[0]["county"]), response_data[1])
#         self.assertIn((data[0]["price"]), response_data[1])
#         self.assertIn((data[0]["price_per_m2"]), response_data[1])
#         self.assertIn((data[0]["area"]), response_data[1])
#         self.assertIn((data[0]["link"]), response_data[1])
#         self.assertIn((data[0]["date_added"]), response_data[1])
#
#         self.assertIn((data[1]["place"]), response_data[3])
#         self.assertIn((data[1]["county"]), response_data[3])
#         self.assertIn((data[1]["price"]), response_data[3])
#         self.assertIn((data[1]["price_per_m2"]), response_data[3])
#         self.assertIn((data[1]["area"]), response_data[3])
#         self.assertIn((data[1]["link"]), response_data[3])
#         self.assertIn((data[1]["date_added"]), response_data[3])
#
#     def test_sending_csv_view(self):
#         response = self.client.post(
#             reverse("parcels:sending_csv", kwargs=self.test_data)
#         )
#
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(len(mail.outbox), 1)
#         self.assertEqual(mail.outbox[0].subject, "ParcelsScraper - wybrane działki")
#         self.assertEqual(
#             mail.outbox[0].body, "W załączeniu przesyłamy wybrane przez Ciebie działki."
#         )
#
#         self.assertIn((data[0]["place"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["county"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["price"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["price_per_m2"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["area"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["link"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[0]["date_added"]), mail.outbox[0].attachments[0][1])
#
#         self.assertIn((data[1]["place"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["county"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["price"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["price_per_m2"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["area"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["link"]), mail.outbox[0].attachments[0][1])
#         self.assertIn((data[1]["date_added"]), mail.outbox[0].attachments[0][1])
