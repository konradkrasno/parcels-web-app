from typing import *

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet

from parcels.models import Advert, Favourite


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


def get_adverts(request: WSGIRequest) -> QuerySet:
    if request.session.get("view_name", None) == "favourites":
        search_text = request.GET.get("search_text", None)
        return Favourite.get_favourites(
            user_id=request.user.id, search_text=search_text
        )
    return Advert.filter_adverts(
        place=request.GET.get("place", None),
        price=request.GET.get("price", 0),
        area=request.GET.get("area", 0),
        search_text=request.GET.get("search_text", None),
    )
