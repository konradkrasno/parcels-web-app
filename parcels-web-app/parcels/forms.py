from typing import *

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Advert
from .validators import validate_positive


class AdvertForm(forms.Form):
    place = forms.CharField(
        max_length=250,
        label="Miejscowość",
        help_text="Podaj lokalizację działki",
        required=False,
    )
    price = forms.IntegerField(
        label="Cena", help_text="Podaj maksymalną cenę", required=False, validators=[validate_positive]
    )
    area = forms.IntegerField(
        label="Powierzchnia", help_text="Podaj minimalną powierzchnię", required=False, validators=[validate_positive]
    )

    class Meta:
        model = Advert
        fields = ("place", "price", "area")

    def clean(self):
        data = super().clean()
        for key, val in data.items():
            if val == '':
                data[key] = 'None'
            elif val is None:
                data[key] = 0
        return data


class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=150, label="Nazwa użytkownika")
    password1 = forms.CharField(label="Hasło", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Potwierdź hasło", widget=forms.PasswordInput)

    email1 = forms.EmailField(label="Email", widget=forms.EmailInput)
    email2 = forms.EmailField(label="Potwierdź email", widget=forms.EmailInput)

    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_email2(self) -> str:
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")
        if email1 and email2 and email1 != email2:
            raise forms.ValidationError("Podane adresy email są niezgodne")
        return email2


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Nazwa użytkownika")
    password = forms.CharField(label="Hasło", widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ("username",)
