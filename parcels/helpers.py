import os
import re
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


def get_web_container_host() -> str:
    MAIN_DIR = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )
    )
    HOSTS_DIR = os.path.join(MAIN_DIR, "etc/hosts")
    try:
        with open(HOSTS_DIR) as f:
            host = re.match(r"([0-9]*(\.))*", list(f).pop()).group() + "1"
    except FileNotFoundError:
        host = "127.0.0.1"
    return host
