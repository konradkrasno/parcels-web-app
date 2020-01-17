from django import forms
from django.contrib.auth.models import User
from .models import Advert


class AdvertForm(forms.ModelForm):
    place = forms.CharField(max_length=250, help_text='Podaj lokalizację działki', required=True)
    price = forms.FloatField(help_text='Podaj maksymalną cenę', required=True)
    area = forms.FloatField(help_text='Podaj minimalną powierzchnię', required=True)

    class Meta:
        model = Advert
        fields = ('place', 'price', 'area')


class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=250, label='Nazwa użytkownika', required=True)
    password = forms.CharField(widget=forms.PasswordInput, label='Hasło', required=True)
    email = forms.EmailField(label='Adres email', required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email')
