from django import forms
from django.contrib.auth import get_user_model
from .models import Advert

from django.contrib.auth.forms import UserCreationForm


class AdvertForm(forms.ModelForm):
    place = forms.CharField(
        max_length=250, help_text="Podaj lokalizację działki", required=True
    )
    price = forms.IntegerField(help_text="Podaj maksymalną cenę", required=True)
    area = forms.IntegerField(help_text="Podaj minimalną powierzchnię", required=True)

    class Meta:
        model = Advert
        fields = ("place", "price", "area")


class SignUp(UserCreationForm):
    username = forms.CharField(max_length=150, label="Nazwa użytkownika")
    password1 = forms.CharField(label="Hasło", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Potwierdź hasło", widget=forms.PasswordInput)

    email1 = forms.EmailField(label="Email", widget=forms.EmailInput)
    email2 = forms.EmailField(label="Potwierdź email", widget=forms.EmailInput)

    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_email2(self):
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")
        if email1 and email2 and email1 != email2:
            raise forms.ValidationError("Podane adresy email są niezgodne")
        return email2
