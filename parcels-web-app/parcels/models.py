import logging
import os
import re
import pandas as pd
import glob

from django.core.validators import validate_comma_separated_integer_list
from django.db import models, transaction

from django.db.utils import ProgrammingError, IntegrityError
from django.db.models import QuerySet

from typing import Union

logging.basicConfig(level=logging.DEBUG)


class Advert(models.Model):
    """ Model stores scraped adverts data. """

    place = models.CharField(max_length=250, null=True)
    county = models.CharField(max_length=250, null=True)
    price = models.FloatField(null=True)
    price_per_m2 = models.FloatField(default=0, null=True)
    area = models.FloatField(null=True)
    link = models.CharField(max_length=2000, null=True)
    date_added = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)

    def __str__(self):
        return "{}, price: {} PLN, area: {} PLN/m2".format(
            self.place, self.price, self.area
        )

    @classmethod
    def load_adverts(cls, catalog: str):
        """
        Load data from files and save to database.

        :param catalog: Catalog name in current working directory with files to added
        """

        path = os.path.join(os.getcwd(), catalog, "*.csv")
        files = glob.glob(path)

        if files:
            for file in files:
                adv = pd.read_csv(file)

                try:
                    for item in adv.values:
                        try:
                            with transaction.atomic():
                                cls(
                                    place=item[0],
                                    county=item[1],
                                    price=item[2],
                                    price_per_m2=item[3],
                                    area=item[4],
                                    link=item[5],
                                    date_added=item[6],
                                    description=item[7]
                                ).save()
                        except ValueError as e:
                            logging.error(e)

                except ProgrammingError:
                    raise ProgrammingError("You have to make migrations before add data to database.")
        else:
            raise FileNotFoundError("No files to added.")

        logging.info("Data successfully updated.")

    @classmethod
    def delete_duplicates(cls):
        """ Delete duplicates objects from database. """

        min_id_objects = cls.objects.values(
            "place", "price", "price_per_m2", "area"
        ).annotate(minid=models.Min("id"))
        min_ids = [obj["minid"] for obj in min_id_objects]

        cls.objects.exclude(id__in=min_ids).delete()

        logging.info(
            "Amount of adverts after deleting duplicates: {}".format(
                len(cls.objects.all())
            )
        )

    @classmethod
    def filter_adverts(cls, place: str, price: int, area: int) -> QuerySet:
        """ Return objects filtered by place, price and area ordered by price. """

        return cls.objects.filter(place=place,
                                  price__lte=price,
                                  area__gte=area,
                                  ).order_by('price')


class Favourite(models.Model):
    """ Model stores information about adverts saved by user to favourite. """

    user_id = models.IntegerField(unique=True)
    favourite = models.CharField(
        validators=[validate_comma_separated_integer_list], max_length=10000
    )

    def __str__(self):
        return "{}: {}".format(self.user_id, self.favourite)

    def add_to_favourite(self, pk: int):
        """ Add object pk to list of favourite. """

        if self.user_id:
            if not self.favourite:
                self.favourite = "{}".format(pk)
            elif re.search("{}".format(pk), self.favourite) is None:
                self.favourite = self.favourite + ",{}".format(pk)
        else:
            raise IntegrityError("No user id assigned to Favourite model instance.")

    def delete_from_favourite(self, pk: int):
        """ Delete object pk from list of favourite. """

        if re.search(",{0},".format(pk), self.favourite):
            self.favourite = re.sub(",{0},".format(pk), ",", self.favourite)
        else:
            self.favourite = re.sub(",{0}$|^{0},|^{0}$".format(pk), "", self.favourite)

    @classmethod
    def get_favourite_ids(cls, user_id: int) -> list:
        """ Get list of favourite objects depended on user_id. """
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            return list()

        return [int(s) for s in str(favourite.favourite).split(",")]

    @classmethod
    def create_or_update(cls, user_id: int, adverts: Union[list, QuerySet]):
        """ Creates Favourite instance when not exists or updates existing one. """
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            favourite = cls(user_id=user_id)

        if type(adverts) == list:
            for advert in adverts:
                favourite.add_to_favourite(pk=advert)
        else:
            for advert in adverts:
                favourite.add_to_favourite(pk=advert.pk)
        favourite.save()

    @classmethod
    def remove_from_favourite(cls, user_id: int, adverts: Union[list, QuerySet]):
        """ Delete list of objects pk from Favourite instance attribute. """
        try:
            favourite = cls.objects.get(user_id=user_id)
        except cls.DoesNotExist:
            pass
        else:
            if type(adverts) == list:
                for advert in adverts:
                    favourite.delete_from_favourite(pk=advert)
            else:
                for advert in adverts:
                    favourite.delete_from_favourite(pk=advert.pk)
            favourite.save()
