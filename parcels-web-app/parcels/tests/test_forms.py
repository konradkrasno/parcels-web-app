import pytest

from ..forms import AdvertForm


@pytest.mark.django_db
class TestForms:
    """ Class for testing Django forms. """

    pytestmark = pytest.mark.django_db

    def test_advert_form_when_valid(self):
        form = AdvertForm(
            data={
                "place": "Warszawa",
                "price": "500000",
                "area": "1000",
            }
        )

        assert form.is_valid()

    def test_advert_form_when_invalid(self):
        form = AdvertForm(
            data={
                "price": "500000",
                "area": "1000",
            }
        )
        assert not form.is_valid()

    def test_sign_up_form_when_valid(self):
        form = SignUp(
            data={
                "username": "test_user",
                "password1": "secret132",
                "password2": "secret132",
                "email1": "test@gmail.com",
                "email2": "test@gmail.com",
            }
        )
        assert form.is_valid()

    def test_sign_up_form_when_invalid(self):
        form = SignUp(
            data={
                "username": "test_user",
                "password1": "password",
                "password2": "password",
                "email1": "test@gmail.com",
                "email2": "test@gmail.com",
            }
        )
        assert not form.is_valid()
