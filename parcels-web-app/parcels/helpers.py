from typing import *

from django.db.models import QuerySet


class Echo:
    """ Helper class for streaming csv file. """

    @staticmethod
    def write(value):
        return value


def prepare_csv(adverts: QuerySet) -> List:
    rows = [
        [
            "Miejscowość",
            "Powiat",
            "Cena",
            "Cena za m2",
            "Powierzchnia",
            "Link",
            "Data dodania",
        ]
    ]
    for adv in adverts:
        row = [
            adv.place,
            adv.county,
            adv.price,
            adv.price_per_m2,
            adv.area,
            adv.link,
            adv.date_added,
        ]
        rows.append(row)
    return rows
