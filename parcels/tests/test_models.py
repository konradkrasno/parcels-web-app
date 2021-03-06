import os
from collections.abc import Iterable

import pytest

from parcels.models import Advert, Favourite
from parcels.tests.conftest import (
    TEST_DIR,
)


@pytest.mark.django_db
class TestAdvert:
    """ Class for testing Advert's model methods. """

    pytestmark = pytest.mark.django_db

    def test_load_adverts(self, create_test_csv):
        Advert.load_adverts(TEST_DIR)
        assert Advert.objects.exists()

    def test_load_adverts_when_no_files(self):
        try:
            os.remove(os.path.join(os.getcwd(), TEST_DIR, "test_data.csv"))
        except FileNotFoundError:
            pass

        with pytest.raises(FileNotFoundError):
            Advert.load_adverts(TEST_DIR)

    def test_delete_duplicates(self):
        actual_data = [obj["place"] for obj in Advert.objects.values("place")]
        expected_data = ["Dębe Wielkie", "Rysie", "Rysie"]
        assert actual_data == expected_data

    def test_get_adverts_when_advert_do_not_exist(self):
        assert not Advert.get_advert(500)

    def test_filter_adverts(self):
        assert (
            Advert.filter_adverts(place="Dębe Wielkie", price=400000, area=800).values(
                "place"
            )[0]["place"]
            == "Dębe Wielkie"
        )

        assert (
            Advert.filter_adverts(place="None", price=200000, area=1000).values(
                "place"
            )[0]["place"]
            == "Rysie"
        )

    def test_search_text(self):
        adverts = Advert.objects.all()
        assert Advert.search_by_description(adverts, "media przy działce")

    def test_get_places(self):
        assert len(Advert.get_places()) == 2


@pytest.mark.django_db
class TestFavourite:
    """ Class for testing Favourite model and its methods. """

    pytestmark = pytest.mark.django_db

    def test_add_to_favourite(self, user, test_adverts):
        Favourite.add_to_favourite(user_id=user.id, adverts=test_adverts)
        added_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        expected_adverts = test_adverts.values_list("place", "price", "area")
        assert list(added_adverts) == list(expected_adverts)

    def test_add_to_favourite_with_empty_list(self, user):
        Favourite.add_to_favourite(user_id=user.id, adverts=[])
        added_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        assert list(added_adverts) == [(None, None, None)]

    def test_remove_from_favourite(self, user, test_adverts, add_favourites):
        advert = Advert.objects.filter(place="Dębe Wielkie")
        Favourite.remove_from_favourite(user_id=user.id, adverts=advert)
        result_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        expected_adverts = test_adverts.exclude(place="Dębe Wielkie").values_list(
            "place", "price", "area"
        )
        assert list(result_adverts) == list(expected_adverts)
        assert len(result_adverts) == 2

    def test_remove_from_favourite_with_empty_list(
        self, user, test_adverts, add_favourites
    ):
        Favourite.remove_from_favourite(user_id=user.id, adverts=[])
        result_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        expected_adverts = test_adverts.values_list("place", "price", "area")
        assert list(result_adverts) == list(expected_adverts)
        assert len(result_adverts) == 3

    def test_remove_from_favourite_when_object_not_in_favourites(
        self, user, test_adverts
    ):
        advert = Advert.objects.filter(place="Dębe Wielkie")
        Favourite.remove_from_favourite(user_id=user.id, adverts=advert)
        result_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        assert list(result_adverts) == []
        assert len(result_adverts) == 0

    def test_get_favourites(self, user, test_adverts, add_favourites):
        result_adverts = Favourite.get_favourites(user_id=user.id)
        for result, expected in zip(result_adverts, test_adverts):
            assert result == expected
        assert len(result_adverts) == 3

    def test_get_favourites_when_user_do_not_exist(self):
        result_advert = Favourite.get_favourites(user_id=100)
        assert list(result_advert) == []
        assert isinstance(result_advert, Iterable)
