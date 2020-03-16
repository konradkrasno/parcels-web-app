from django.shortcuts import reverse
from django.core import mail
from django.test import TestCase, RequestFactory, Client

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from ..tokens import account_activation_token

from django.contrib.auth.models import User

from ..models import Advert, Favourite

from .. import views

from .test_data import data

# Create your tests here.


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()

    def test_user_login(self):
        response = self.client.post('/user_login', {'username': 'test_user', 'password': 'password'})
        self.assertEqual(response.status_code, 302)

    def test_user_logout(self):
        client_login = self.client.login(username='test_user', password='password')
        self.assertTrue(client_login, "Client not login")
        response = self.client.post(reverse('parcels:logout'))
        self.assertEquals(response.status_code, 302)


class IndexTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse('parcels:index'))
        self.assertEqual(response.status_code, 200)


class SearchAdvertWhenLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.context = {'user_id': 1}
        self.valid_test_data = {
            'place': 'Dębe Wielkie',
            'price': 200000,
            'area': 1000
        }
        self.invalid_test_data = {
            'price': 200000,
            'area': 1000
        }

    def test_get(self):
        response = self.client.get(reverse('parcels:form_when_login', kwargs=self.context))
        self.assertEqual(response.status_code, 200)

    def test_post_if_form_is_valid(self):
        request = self.factory.post(reverse('parcels:form_when_login', kwargs=self.context), data=self.valid_test_data)
        view = views.SearchAdvertWhenLoginView()
        response = view.post(request=request, user_id=self.context["user_id"])

        self.assertEqual(response.status_code, 302)
        self.assertIn('200000', response.url)
        self.assertIn('1000', response.url)

    def test_post_if_form_is_invalid(self):
        request = self.factory.post(reverse('parcels:form_when_login', kwargs=self.context), data=self.invalid_test_data)
        view = views.SearchAdvertWhenLoginView()
        response = view.post(request=request, user_id=self.context["user_id"])

        self.assertEqual(response.status_code, 200)


class SearchAdvertWhenLogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.valid_test_data = {
            'place': 'Dębe Wielkie',
            'price': 200000,
            'area': 1000
        }

        self.invalid_test_data = {
            'price': 200000,
            'area': 1000
        }

    def test_get(self):
        response = self.client.get(reverse('parcels:form_when_logout'))
        self.assertEqual(response.status_code, 200)

    def test_post_if_form_is_valid(self):
        request = self.factory.post(reverse('parcels:form_when_logout'), data=self.valid_test_data)
        view = views.SearchAdvertWhenLogoutView()
        response = view.post(request=request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('200000', response.url)
        self.assertIn('1000', response.url)

    def test_post_if_form_is_invalid(self):
        request = self.factory.post(reverse('parcels:form_when_logout'), data=self.invalid_test_data)
        view = views.SearchAdvertWhenLogoutView()
        response = view.post(request=request)

        self.assertEqual(response.status_code, 200)


class AdvertListWhenLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 800,
            'user_id': 1,
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:advert_list_when_login', kwargs=self.test_data))
        view = views.AdvertListWhenLoginView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:advert_list_when_login', kwargs=self.test_data))
        view = views.AdvertListWhenLoginView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('place', context)
        self.assertIn('price', context)
        self.assertIn('area', context)
        self.assertEqual(context["advert_list"].values("link")[0]["link"], data[0]["link"])


class AdvertListWhenLogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 800,
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:advert_list_when_logout', kwargs=self.test_data))
        view = views.AdvertListWhenLogoutView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:advert_list_when_logout', kwargs=self.test_data))
        view = views.AdvertListWhenLogoutView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('place', context)
        self.assertIn('price', context)
        self.assertIn('area', context)
        self.assertEqual(context["advert_list"].values("link")[0]["link"], data[0]["link"])


class AdvertDetailWhenLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 800,
            'pk': 1,
            'user_id': 1,
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:advert_detail_when_login', kwargs=self.test_data))
        view = views.AdvertDetailWhenLoginView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:advert_detail_when_login', kwargs=self.test_data))
        view = views.AdvertDetailWhenLoginView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('place', context)
        self.assertIn('price', context)
        self.assertIn('area', context)
        self.assertEqual(context["object"].values("link")[0]["link"], data[0]["link"])


class AdvertDetailWhenLogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 800,
            'pk': 1,
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:advert_detail_when_logout', kwargs=self.test_data))
        view = views.AdvertDetailWhenLogoutView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:advert_detail_when_logout', kwargs=self.test_data))
        view = views.AdvertDetailWhenLogoutView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('place', context)
        self.assertIn('price', context)
        self.assertIn('area', context)
        self.assertEqual(context["object"].values("link")[0]["link"], data[0]["link"])


class FavouriteListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.test_data = {'user_id': 1}

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=1, user_id=1)
        favourite.add_to_favourite(pk=2)
        favourite.save()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:favourite_list', kwargs=self.test_data))
        view = views.FavouriteListView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:favourite_list', kwargs=self.test_data))
        view = views.FavouriteListView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('fav_id', context)
        self.assertEqual(context["advert_list"].values("link")[0]["link"], data[0]["link"])


class FavouriteDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.test_data = {
            'pk': 1,
            'user_id': 1,
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()
        Advert.delete_duplicates()

        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=1, user_id=1)
        favourite.add_to_favourite(pk=2)
        favourite.save()

    def test_get_queryset(self):
        request = RequestFactory().get(reverse('parcels:favourite_detail', kwargs=self.test_data))
        view = views.FavouriteDetailView()
        view.setup(request)
        view.kwargs = self.test_data

        query = view.get_queryset()
        self.assertEqual(query.values("link")[0]["link"], data[0]["link"])

    def test_context_data(self):
        request = RequestFactory().get(reverse('parcels:favourite_detail', kwargs=self.test_data))
        view = views.FavouriteDetailView()
        view.setup(request)
        view.kwargs = self.test_data

        context = view.get_context_data()
        self.assertIn('fav_id', context)
        self.assertEqual(context["object"].values("link")[0]["link"], data[0]["link"])


class RegisterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.valid_data = {
            'username': 'test_user',
            'password1': 'zorro132',
            'password2': 'zorro132',
            'email1': 'test@gmail.com',
            'email2': 'test@gmail.com'
        }

        self.invalid_data = {
            'username': 'test_user',
            'password1': 'password',
            'password2': 'password',
            'email1': 'test@gmail.com',
            'email2': 'test@gmail.com'
        }

    def test_register_if_form_is_valid(self):
        response = self.client.post('/register', data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.values('username')[0]['username'], 'test_user')
        self.assertEqual(User.objects.values('email')[0]['email'], 'test@gmail.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Aktywacja konta w aplikacji ParcelsScraper')

    def test_register_if_form_is_invalid(self):
        response = self.client.post('/register', data=self.invalid_data)
        self.assertEqual(response.status_code, 200)

    def test_activate(self):
        user = User.objects.create(username="test_user", email="test@gmail.com")
        user.set_password('password')
        user.is_active = False
        user.save()

        test_activate_data = {
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user)
        }

        response = self.client.get(reverse('parcels:activate', kwargs=test_activate_data), data=test_activate_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(pk=user.pk).is_active, 'User is inactive.')


class MakeFavouriteTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()

    def test_make_favourite(self):
        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:make_favourite', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '100')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('100', response.url)
        self.assertIn('1', response.url)

    def test_make_favourite_list(self):
        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:make_favourite_list', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '100')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('1', response.url)

    def test_make_all_favourite(self):
        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:make_all_favourite', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '1,3,4')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('1', response.url)

    def test_make_favourite_from_fav(self):
        test_data = {
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:make_favourite_from_fav', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '100')
        self.assertIn('100', response.url)
        self.assertIn('1', response.url)

    def test_remove_favourite(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_favourite', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '101')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('100', response.url)
        self.assertIn('1', response.url)

    def test_remove_favourite_list(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_favourite_list', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '101')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('1', response.url)

    def test_remove_all_favourite(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=1, user_id=1)
        favourite.add_to_favourite(pk=2)
        favourite.add_to_favourite(pk=3)
        favourite.add_to_favourite(pk=4)
        favourite.add_to_favourite(pk=5)
        favourite.save()

        test_data = {
            'place': "Dębe Wielkie",
            'price': 400000,
            'area': 1000,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_all_favourite', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '2,5')
        self.assertIn('400000', response.url)
        self.assertIn('1000', response.url)
        self.assertIn('1', response.url)

    def test_remove_favourite_from_fav(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        test_data = {
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_favourite_from_fav', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '101')
        self.assertIn('100', response.url)
        self.assertIn('1', response.url)

    def test_remove_favourite_from_fav_list(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        test_data = {
            'pk': 100,
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_favourite_from_fav_list', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '101')
        self.assertIn('1', response.url)

    def test_remove_all_favourite_from_fav(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.add_to_favourite(pk=102)
        favourite.add_to_favourite(pk=103)
        favourite.add_to_favourite(pk=104)
        favourite.save()

        test_data = {
            'user_id': self.user.id
        }

        response = self.client.post(reverse('parcels:remove_all_favourite_from_fav', kwargs=test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.values("favourite")[0]["favourite"], '')
        self.assertIn('1', response.url)


class CSVTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.user = User.objects.create(username="test_user", email="test@gmail.com")
        self.user.set_password('password')
        self.user.save()
        self.client.login(username="test_user", password="password")

        self.test_data = {
            'user_id': self.user.id
        }

        Advert.objects.all().delete()
        for item in data:
            advert = Advert(**item)
            advert.save()

        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=1, user_id=1)
        favourite.add_to_favourite(pk=2)
        favourite.add_to_favourite(pk=3)
        favourite.add_to_favourite(pk=5)
        favourite.save()

    def test_streaming_csv_view(self):
        response = self.client.post(reverse('parcels:streaming_csv', kwargs=self.test_data))

        response_data = []
        for row in response:
            response_data.append(str(row, encoding='utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.get('Content-Disposition'), '''attachment; filename="your_adverts.csv"''')
        self.assertIn((data[0]["place"]), response_data[1])
        self.assertIn((data[0]["county"]), response_data[1])
        self.assertIn((data[0]["price"]), response_data[1])
        self.assertIn((data[0]["price_per_m2"]), response_data[1])
        self.assertIn((data[0]["area"]), response_data[1])
        self.assertIn((data[0]["link"]), response_data[1])
        self.assertIn((data[0]["date_added"]), response_data[1])

        self.assertIn((data[1]["place"]), response_data[3])
        self.assertIn((data[1]["county"]), response_data[3])
        self.assertIn((data[1]["price"]), response_data[3])
        self.assertIn((data[1]["price_per_m2"]), response_data[3])
        self.assertIn((data[1]["area"]), response_data[3])
        self.assertIn((data[1]["link"]), response_data[3])
        self.assertIn((data[1]["date_added"]), response_data[3])

    def test_sending_csv_view(self):
        response = self.client.post(reverse('parcels:sending_csv', kwargs=self.test_data))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'ParcelsScraper - wybrane działki')
        self.assertEqual(mail.outbox[0].body, 'W załączeniu przesyłamy wybrane przez Ciebie działki.')

        self.assertIn((data[0]["place"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["county"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["price"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["price_per_m2"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["area"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["link"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[0]["date_added"]), mail.outbox[0].attachments[0][1])

        self.assertIn((data[1]["place"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["county"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["price"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["price_per_m2"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["area"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["link"]), mail.outbox[0].attachments[0][1])
        self.assertIn((data[1]["date_added"]), mail.outbox[0].attachments[0][1])
