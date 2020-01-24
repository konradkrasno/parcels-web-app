from django.core.validators import validate_comma_separated_integer_list
from django.db import models
import json
import re

# Create your models here.


class Advert(models.Model):
    store_id = models.PositiveIntegerField()
    place = models.CharField(max_length=250)
    county = models.CharField(max_length=250)
    price = models.FloatField()
    price_per_m2 = models.FloatField(default=0)
    area = models.FloatField()
    link = models.CharField(max_length=2000)
    date_added = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return '{}, price: {} PLN, area: {} PLN/m2'.format(self.place, self.price, self.area)

    @classmethod
    def download_adverts_from_json(cls):
        with open("adverts.json", "r") as file1:
            adv = json.load(file1)

        for item in adv:
            advert = cls(**item)
            advert.save()

            # Deleting duplicates
            # sq = Advert.object.query(cls.id).group_by(cls.place, cls.price, cls.price_per_m2, cls.area).distinct()
            # query = Advert.__table__.delete().where(cls.id.notin_(sq))

    @classmethod
    def filter_adverts(cls, price, place, area):
        return Advert.objects.filter(place=place,
                                     price__lte=price,
                                     area__gte=area,
                                     ).order_by('price')


class Favourite(models.Model):
    user_id = models.IntegerField(unique=True)
    favourite = models.CharField(validators=[validate_comma_separated_integer_list], max_length=2000)

    def __str__(self):
        return '{}: {}'.format(self.user_id, self.favourite)

    def add_to_favourite_first_time(self, pk, user_id):
        self.user_id = user_id
        self.favourite = pk
        self.save()

    def add_to_favourite(self, pk):
        if self.favourite is '':
            self.favourite = '{}'.format(pk)
        elif re.search('{}'.format(pk), self.favourite) is None:
            self.favourite = self.favourite + ',{}'.format(pk)

    def delete_from_favourite(self, pk):
        if re.search(',{0},'.format(pk), self.favourite):
            self.favourite = re.sub(',{0},'.format(pk), ',', self.favourite)
        else:
            self.favourite = re.sub(',{0}$|^{0},|^{0}$'.format(pk), '', self.favourite)

    @classmethod
    def get_fav_id(cls, user_id):
        try:
            favourite = Favourite.objects.get(user_id=user_id)
            return [int(s) for s in str(favourite.favourite).split(',')]
        except:
            return []

    @classmethod
    def make_favourite(cls, pk, user_id):
        try:
            favourite = Favourite.objects.get(user_id=user_id)
            favourite.add_to_favourite(pk=pk)
            favourite.save()
        except:
            favourite = Favourite()
            favourite.add_to_favourite_first_time(pk=pk, user_id=user_id)

    @classmethod
    def make_many_favourite(cls, user_id, adverts):
        favourite = Favourite()

        for i, advert in enumerate(adverts):
            pk = advert.pk
            if i == 0:
                try:
                    favourite = Favourite.objects.get(user_id=user_id)
                    favourite.add_to_favourite(pk=pk)
                except:
                    favourite.add_to_favourite_first_time(pk=pk, user_id=user_id)
                    favourite = Favourite.objects.get(user_id=user_id)
            else:
                favourite.add_to_favourite(pk=pk)
        favourite.save()

    @classmethod
    def remove_favourite(cls, pk, user_id):
        try:
            favourite = Favourite.objects.get(user_id=user_id)
            favourite.delete_from_favourite(pk=pk)
            favourite.save()
        except:
            pass

    @classmethod
    def remove_many_favourite(cls, user_id, adverts):
        try:
            favourite = Favourite.objects.get(user_id=user_id)
            for advert in adverts:
                pk = advert.pk
                favourite.delete_from_favourite(pk=pk)
            favourite.save()
        except:
            pass

    @classmethod
    def remove_many_favourite_from_fav(cls, user_id, pk_list):
        try:
            favourite = Favourite.objects.get(user_id=user_id)
            for pk in pk_list:
                favourite.delete_from_favourite(pk=pk)
            favourite.save()
        except:
            pass
