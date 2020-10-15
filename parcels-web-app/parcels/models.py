import logging
import json
import re

from django.core.validators import validate_comma_separated_integer_list
from django.db import models

logging.basicConfig(level=logging.DEBUG)


class Advert(models.Model):
    store_id = models.PositiveIntegerField(null=True)
    place = models.CharField(max_length=250, null=True)
    county = models.CharField(max_length=250, null=True)
    price = models.FloatField(null=True)
    price_per_m2 = models.FloatField(default=0, null=True)
    area = models.FloatField(null=True)
    link = models.CharField(max_length=2000, null=True)
    date_added = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)

    def __str__(self):
        return '{}, price: {} PLN, area: {} PLN/m2'.format(self.place, self.price, self.area)

    @classmethod
    def download_adverts_from_json(cls):
        try:
            with open("adverts.json", "r") as file:
                adv = json.load(file)
        except FileNotFoundError:
            logging.error("Can not find file adverts.json")

        else:
            for item in adv:
                advert = cls(**item)
                advert.save()

    @classmethod
    def delete_duplicates(cls):

        # Deleting duplicates
        min_id_objects = cls.objects.values("place", "price", "price_per_m2", "area").annotate(minid=models.Min('id'))
        min_ids = [obj['minid'] for obj in min_id_objects]

        cls.objects.exclude(id__in=min_ids).delete()

        logging.info("Amount of adverts after deleting duplicates: {}".format(len(cls.objects.all())))

    @classmethod
    def filter_adverts(cls, price, place, area):
        return cls.objects.filter(place=place,
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
        self.favourite = '{}'.format(pk)

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
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            return []

        return [int(s) for s in str(favourite.favourite).split(',')]

    @classmethod
    def make_favourite(cls, pk, user_id):
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            favourite = cls()
            favourite.add_to_favourite_first_time(pk=pk, user_id=user_id)
        else:
            favourite.add_to_favourite(pk=pk)

        favourite.save()

    @classmethod
    def make_many_favourite(cls, user_id, adverts):
        favourite = cls()

        for i, advert in enumerate(adverts):
            pk = advert.pk
            if i == 0:
                try:
                    favourite = cls.objects.get(user_id=user_id)
                except Favourite.DoesNotExist:
                    favourite.add_to_favourite_first_time(pk=pk, user_id=user_id)
                else:
                    favourite.add_to_favourite(pk=pk)

            else:
                favourite.add_to_favourite(pk=pk)
        favourite.save()

    @classmethod
    def remove_favourite(cls, pk, user_id):
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            pass
        else:
            favourite.delete_from_favourite(pk=pk)
            favourite.save()

    @classmethod
    def remove_many_favourite(cls, user_id, adverts):
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            pass
        else:
            for advert in adverts:
                pk = advert.pk
                favourite.delete_from_favourite(pk=pk)
            favourite.save()

    @classmethod
    def remove_many_favourite_from_fav(cls, user_id, pk_list):
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            pass
        else:
            for pk in pk_list:
                favourite.delete_from_favourite(pk=pk)
            favourite.save()
