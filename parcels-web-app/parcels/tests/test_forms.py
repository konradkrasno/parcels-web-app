from django.test import TestCase, Client

from parcels.forms import AdvertForm, SignUp

# Create your tests here.


class AdvertFormTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_advert_form_form_valid(self):
        form = AdvertForm(data={
            'place': 'Warszawa',
            'price': '500000',
            'area': '1000',
        })
        self.assertTrue(form.is_valid())

    def test_advert_form_form_invalid(self):
        form = AdvertForm(data={
            'price': '500000',
            'area': '1000',
        })
        self.assertFalse(form.is_valid())


class SignUpTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sign_up_form_valid(self):
        form = SignUp(data={'username': 'test_user',
                            'password1': 'zorro132',
                            'password2': 'zorro132',
                            'email1': 'test@gmail.com',
                            'email2': 'test@gmail.com'})
        self.assertTrue(form.is_valid())

    def test_sign_up_form_invalid(self):
        form = SignUp(data={'username': 'test_user',
                            'password1': 'password',
                            'password2': 'password',
                            'email1': 'test@gmail.com',
                            'email2': 'test@gmail.com'})
        self.assertFalse(form.is_valid())
