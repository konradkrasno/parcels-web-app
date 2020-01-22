from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site

from django.template.loader import render_to_string

from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import View, TemplateView
from .models import Advert, Favourite
from .forms import AdvertForm, SighUp

from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import account_activation_token

import csv
from io import StringIO

# Create your views here.


class Index(TemplateView):
    template_name = 'parcels/index.html'

    # model.download_adverts_from_json()


class SearchAdvertWhenLoginView(LoginRequiredMixin, View):
    template_name = 'parcels/advert_form.html'
    form_class = AdvertForm

    def get(self, request, user_id):
        form = self.form_class()
        return render(request, 'parcels/advert_form.html', {'form': form})

    def post(self, request, user_id):
        favourite = Favourite()
        fav_id = favourite.get_fav_id(user_id=user_id)

        form = self.form_class(request.POST)

        if form.is_valid():
            place = form.cleaned_data['place']
            price = form.cleaned_data['price']
            area = form.cleaned_data['area']

            return HttpResponseRedirect('{}/{}/{}/{}'.format(place, price, area, user_id), {'place': place,
                                                                                            'price': price,
                                                                                            'area': area,
                                                                                            'fav_id': fav_id
                                                                                            })

        else:
            form = AdvertForm()
        return render(request, 'parcels/advert_form.html', {'form': form})


class SearchAdvertWhenLogoutView(View):
    template_name = 'parcels/advert_form.html'
    form_class = AdvertForm

    def get(self, request):
        form = self.form_class()
        return render(request, 'parcels/advert_form.html', {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            place = form.cleaned_data['place']
            price = form.cleaned_data['price']
            area = form.cleaned_data['area']

            return HttpResponseRedirect('form/logout/{}/{}/{}'.format(place, price, area), {'place': place,
                                                                                            'price': price,
                                                                                            'area': area,
                                                                                            })

        else:
            form = AdvertForm()
        return render(request, 'parcels/advert_form.html', {'form': form})


class AdvertListWhenLoginView(LoginRequiredMixin, View):
    template_name = 'parcels/advert_list.html'

    @classmethod
    def get(cls, request, place, price, area, user_id):
        filtered_adverts = Advert.filter_adverts(price, place, area)

        favourite = Favourite()
        fav_id = favourite.get_fav_id(user_id=user_id)

        all_fav_added = False
        if filtered_adverts:
            filtered_adverts_id = [advert.pk for advert in filtered_adverts]
            if set(filtered_adverts_id) - set(fav_id) == set():
                all_fav_added = True

        content = {'filtered_adverts': filtered_adverts,
                   'fav_id': fav_id,
                   'place': place,
                   'price': price,
                   'area': area,
                   'all_fav_added': all_fav_added
                   }

        return render(request, 'parcels/advert_list.html', context=content)


class AdvertListWhenLogoutView(View):
    template_name = 'parcels/advert_list.html'

    @classmethod
    def get(cls, request, place, price, area):
        filtered_adverts = Advert.filter_adverts(price, place, area)

        content = {'filtered_adverts': filtered_adverts,
                   'place': place,
                   'price': price,
                   'area': area,
                   }

        return render(request, 'parcels/advert_list.html', context=content)


class AdvertDetailWhenLoginView(LoginRequiredMixin, View):
    template_name = 'parcels/advert_detail.html'

    @classmethod
    def get(cls, request, place, price, area, pk, user_id):
        advert = get_object_or_404(Advert, pk=pk)

        favourite = Favourite()
        fav_id = favourite.get_fav_id(user_id=user_id)

        return render(request, 'parcels/advert_detail.html', {'place': place,
                                                              'price': price,
                                                              'area': area,
                                                              'advert': advert,
                                                              'fav_id': fav_id,
                                                              'pk': pk
                                                              })


class AdvertDetailWhenLogoutView(View):
    template_name = 'parcels/advert_detail.html'

    @classmethod
    def get(cls, request, place, price, area, pk):
        advert = get_object_or_404(Advert, pk=pk)

        content = {'place': place,
                   'price': price,
                   'area': area,
                   'advert': advert,
                   'pk': pk
                   }

        return render(request, 'parcels/advert_detail.html', context=content)


class FavouriteListView(LoginRequiredMixin, View):
    template_name = 'parcels/favourite_list.html'
    model = Advert

    @classmethod
    def get(cls, request, user_id):
        favourite = Favourite()
        fav_id = favourite.get_fav_id(user_id=user_id)
        favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

        return render(request, 'parcels/favourite_list.html', {'favourite_list': favourite_list,
                                                               'fav_id': fav_id
                                                               })


class FavouriteDetailView(LoginRequiredMixin, View):
    template_name = 'parcels/fav_advert_detail.html'

    @classmethod
    def get(cls, request, pk, user_id):
        advert = get_object_or_404(Advert, pk=pk)

        favourite = Favourite()
        fav_id = favourite.get_fav_id(user_id=user_id)

        return render(request, 'parcels/fav_advert_detail.html', {'advert': advert,
                                                                  'fav_id': fav_id,
                                                                  'pk': pk
                                                                  })


def register(request):
    if request.method == 'POST':
        user_form = SighUp(data=request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False
            user.email = user_form.clean_email2()
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Aktywacja konta w aplikacji ParcelsScraper'
            message = render_to_string('registration/active_mail.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = user_form.cleaned_data.get('email1')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Potwierź adres email, aby dokończyć rejestrację.')

    else:
        user_form = SighUp()

    return render(request, 'registration/registration.html', {'user_form': user_form,
                                                              })


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        return HttpResponseRedirect(reverse('parcels:login'))
    return HttpResponse('Link aktywacyjny jest nieważny.')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('parcels:index'))
        else:
            return HttpResponse("Złe dane logowania!")
    else:
        return render(request, 'registration/login.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('parcels:index'))


@login_required
def make_favourite(request, place, price, area, pk, user_id):
    advert = get_object_or_404(Advert, pk=pk)

    favourite = Favourite()
    favourite.make_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'advert': advert,
               'place': place,
               'price': price,
               'area': area,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/advert_detail.html', context=content)


@login_required
def make_favourite_list(request, place, price, area, pk, user_id):
    filtered_adverts = Advert.filter_adverts(price, place, area)

    favourite = Favourite()
    favourite.make_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'filtered_adverts': filtered_adverts,
               'place': place,
               'price': price,
               'area': area,
               'pk': pk,
               'fav_id': fav_id,
               }

    return render(request, 'parcels/advert_list.html', context=content)


@login_required
def make_all_favourite(request, place, price, area, user_id):
    filtered_adverts = Advert.filter_adverts(price, place, area)

    favourite = Favourite()
    favourite.make_many_favourite(user_id=user_id, adverts=filtered_adverts)

    fav_id = favourite.get_fav_id(user_id=user_id)
    all_fav_added = True

    content = {'filtered_adverts': filtered_adverts,
               'place': place,
               'price': price,
               'area': area,
               'fav_id': fav_id,
               'all_fav_added': all_fav_added,
               }

    return render(request, 'parcels/advert_list.html', context=content)


@login_required
def make_favourite_from_fav(request, pk, user_id):
    advert = get_object_or_404(Advert, pk=pk)

    favourite = Favourite()
    favourite.make_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'advert': advert,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/fav_advert_detail.html', context=content)


@login_required
def make_favourite_from_fav_list(request, pk, user_id):
    favourite = Favourite()

    favourite.make_favourite(pk=pk, user_id=user_id)

    fav_id = favourite.get_fav_id(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

    content = {'favourite_list': favourite_list,
               'pk': pk,
               'fav_id': fav_id,
               }

    return render(request, 'parcels/favourite_list.html', context=content)


@login_required
def remove_favourite(request, place, price, area, pk, user_id):
    advert = get_object_or_404(Advert, pk=pk)

    favourite = Favourite()
    favourite.remove_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'place': place,
               'price': price,
               'area': area,
               'advert': advert,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/advert_detail.html', context=content)


@login_required
def remove_favourite_list(request, place, price, area, pk, user_id):
    filtered_adverts = Advert.filter_adverts(price, place, area)

    favourite = Favourite()
    favourite.remove_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'filtered_adverts': filtered_adverts,
               'place': place,
               'price': price,
               'area': area,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/advert_list.html', context=content)


@login_required
def remove_all_favourite(request, place, price, area, user_id):
    filtered_adverts = Advert.filter_adverts(price, place, area)

    favourite = Favourite()
    favourite.remove_many_favourite(user_id=user_id, adverts=filtered_adverts)

    fav_id = favourite.get_fav_id(user_id=user_id)
    all_fav_added = False

    content = {'filtered_adverts': filtered_adverts,
               'place': place,
               'price': price,
               'area': area,
               'fav_id': fav_id,
               'all_fav_added': all_fav_added,
               }

    return render(request, 'parcels/advert_list.html', context=content)


@login_required
def remove_favourite_from_fav(request, pk, user_id):
    advert = get_object_or_404(Advert, pk=pk)

    favourite = Favourite()
    favourite.remove_favourite(pk=pk, user_id=user_id)
    fav_id = favourite.get_fav_id(user_id=user_id)

    content = {'advert': advert,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/fav_advert_detail.html', context=content)


@login_required
def remove_favourite_from_fav_list(request, pk, user_id):
    favourite = Favourite()

    favourite.remove_favourite(pk=pk, user_id=user_id)

    fav_id = favourite.get_fav_id(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

    content = {'favourite_list': favourite_list,
               'pk': pk,
               'fav_id': fav_id
               }

    return render(request, 'parcels/favourite_list.html', context=content)


@login_required
def remove_all_favourite_from_fav(request, user_id):
    favourite = Favourite()

    fav_id = favourite.get_fav_id(user_id=user_id)

    favourite.remove_many_favourite_from_fav(user_id=user_id, pk_list=fav_id)

    fav_id = favourite.get_fav_id(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

    content = {'favourite_list': favourite_list,
               'fav_id': fav_id,
               }

    return render(request, 'parcels/favourite_list.html', context=content)


class Echo:
    def write(self, value):
        return value


def streaming_csv_view(request, user_id):
    favourite = Favourite()
    fav_id = favourite.get_fav_id(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

    rows = [['Miejscowość', 'Powiat', 'Cena', 'Cena za m2', 'Powierzchnia', 'Link', 'Data dodania']]
    for adv in favourite_list:
        row = [adv.place, adv.county, adv.price, adv.price_per_m2, adv.area, adv.link, adv.date_added]
        rows.append(row)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="your_adverts.csv"'

    return response


def sending_csv_view(request, user_id):
    favourite = Favourite()
    fav_id = favourite.get_fav_id(user_id=user_id)
    favourite_list = Advert.objects.filter(pk__in=fav_id).order_by('place')

    rows = [['Miejscowość', 'Powiat', 'Cena', 'Cena za m2', 'Powierzchnia', 'Link', 'Data dodania']]
    for adv in favourite_list:
        row = [adv.place, adv.county, adv.price, adv.price_per_m2, adv.area, adv.link, adv.date_added]
        rows.append(row)

    csv_file = StringIO()
    writer = csv.writer(csv_file)
    [writer.writerow(row) for row in rows]

    user = User.objects.get(pk=user_id)
    to_email = user.email

    email = EmailMessage(
        'ParcelsScraper - wybrane działki',
        'W załączeniu przesyłamy wybrane przez Ciebie działki.',
        to=[to_email],
    )
    email.attach('your_adverts.csv', csv_file.getvalue(), "text/csv")
    email.send()

    content = {'user_id': user_id,
               'favourite_list': favourite_list,
               'fav_id': fav_id,
               }

    return render(request, 'parcels/favourite_list.html', context=content)
