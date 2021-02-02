import glob
import logging
import os
from typing import *

import pandas as pd
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import QuerySet
from django.db.utils import ProgrammingError

logging.basicConfig(level=logging.DEBUG)


class Advert(models.Model):
    """ Stores scraped adverts data. """

    place = models.CharField(max_length=250, null=True)
    county = models.CharField(max_length=250, null=True)
    price = models.FloatField(null=True)
    price_per_m2 = models.FloatField(default=0, null=True)
    area = models.FloatField(null=True)
    link = models.CharField(max_length=2000, null=True)
    date_added = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)

    def __repr__(self):
        return "place: {}, price: {} PLN, area: {} PLN/m2".format(
            self.place, self.price, self.area
        )

    @classmethod
    def create(cls, item: list) -> None:
        """ Creates an Advert instance. """
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
                    description=item[7],
                ).save()
        except ValueError as e:
            logging.error(e)

    @classmethod
    def load_adverts(cls, catalog: str) -> None:
        """
        Loads data from files and saves to the database.

        :param catalog: Catalog name with files to be added.
        """

        path = os.path.join(os.getcwd(), catalog, "*.csv")
        files = glob.glob(path)

        if files:
            for file in files:
                adv = pd.read_csv(file)

                try:
                    for item in adv.values:
                        cls.create(item)
                except ProgrammingError:
                    raise ProgrammingError(
                        "You have to make migrations before add data to database."
                    )
        else:
            raise FileNotFoundError("No files to added.")

        logging.info("Data successfully updated.")

    @classmethod
    def delete_duplicates(cls) -> None:
        """ Deletes duplicate objects from the database. """

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
    def get_advert(cls, _id: int):
        return cls.objects.filter(id=_id)

    @classmethod
    def filter_adverts(cls, place: str, price: int, area: int) -> QuerySet:
        """ Returns objects filtered by place, price and area ordered by price. """

        return cls.objects.filter(
            place=place,
            price__lte=price,
            area__gte=area,
        ).order_by("price")


class Favourite(models.Model):
    """ Creates relationships between the user and its favourite adverts. """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    adverts = models.ManyToManyField(Advert)

    def __repr__(self):
        return "user: {}, adverts: {} PLN".format(self.user, self.adverts)

    @staticmethod
    def get_user(user_id: int) -> Union[User, None]:
        """ Gets the user's instance from the database. If not exists returns None. """

        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, user: User):
        """ Gets the instance from the database if it exists. Otherwise creates the new one. """

        while True:
            try:
                return cls.objects.get(user=user)
            except cls.DoesNotExist:
                cls(user=user).save()

    @classmethod
    def add_to_favourite(cls, user_id: int, adverts: Union[list, QuerySet]) -> None:
        """ Adds the relationship between the user and advert. """

        user = cls.get_user(user_id)
        if user:
            fav = cls.get_or_create(user)
            [fav.adverts.add(advert) for advert in adverts]
            fav.save()

    @classmethod
    def remove_from_favourite(
        cls, user_id: int, adverts: Union[list, QuerySet]
    ) -> None:
        """ Removes the relationship between the user and advert. """

        try:
            fav = cls.objects.get(user__id=user_id)
        except cls.DoesNotExist:
            pass
        else:
            [fav.adverts.remove(advert) for advert in adverts]

    @classmethod
    def get_favourites(cls, user_id: int) -> QuerySet:
        """ Returns a list of user's favourites adverts. """

        try:
            return cls.objects.get(user__id=user_id).adverts.all()
        except cls.DoesNotExist:
            return cls.objects.none()
