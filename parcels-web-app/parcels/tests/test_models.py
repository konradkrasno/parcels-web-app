import pytest
import os
import pandas as pd

from parcels.tests.test_data import testing_data
from parcels.models import Advert, Favourite

from django.db.utils import IntegrityError


@pytest.mark.django_db
class TestAdvert:
    """ Class for testing Advert model and its methods. """

    pytestmark = pytest.mark.django_db
    testing_catalog = "fixtures"

    @pytest.fixture
    def create_test_csv(self):
        """ Creates test csv file for testing loading data from file to database. """
        try:
            os.mkdir(os.path.join(os.getcwd(), self.testing_catalog))
        except FileExistsError:
            pass

        header = [
            "place",
            "county",
            "price",
            "price_per_m2",
            "area",
            "link",
            "date_added",
            "description",
        ]
        rows = [item.values() for item in testing_data]
        df = pd.DataFrame(rows, columns=header)
        df.to_csv(
            os.path.join(os.getcwd(), self.testing_catalog, "test_data.csv"),
            index=False,
        )

    @pytest.fixture
    def add_testing_data_to_db(self):
        """Adds data for testing Django models to database."""

        for item in testing_data:
            Advert(**item).save()

        Advert.delete_duplicates()

    def test_load_adverts(self, create_test_csv):
        Advert.load_adverts(self.testing_catalog)
        assert Advert.objects.exists()

    def test_load_adverts_when_no_files(self):
        os.remove(os.path.join(os.getcwd(), self.testing_catalog, "test_data.csv"))
        with pytest.raises(FileNotFoundError):
            Advert.load_adverts(self.testing_catalog)

    def test_delete_duplicates(self, add_testing_data_to_db):
        actual_data = [obj["place"] for obj in Advert.objects.values("place")]
        expected_data = ["Dębe Wielkie", "Rysie"]
        assert actual_data == expected_data

    def test_filter_adverts(self, add_testing_data_to_db):
        assert (
            Advert.filter_adverts(place="Dębe Wielkie", price=400000, area=800).values(
                "place"
            )[0]["place"]
            == "Dębe Wielkie"
        )

        assert (
            Advert.filter_adverts(place="Rysie", price=200000, area=1000).values(
                "place"
            )[0]["place"]
            == "Rysie"
        )


@pytest.mark.django_db
class TestFavourite:
    """ Class for testing Favourite model and its methods. """

    pytestmark = pytest.mark.django_db
    testing_catalog = "fixtures"

    @pytest.fixture
    def favourite(self):
        return Favourite(user_id=1)

    @pytest.fixture
    def add_testing_data_to_db(self):
        """Adds data for testing Django models to database."""

        for item in testing_data:
            Advert(**item).save()

        Advert.delete_duplicates()

    def test_add_to_favourite_when_user_id_set(self, favourite):
        favourite.add_to_favourite(pk=100)
        favourite.add_to_favourite(pk=100)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100"
        }

        favourite.add_to_favourite(pk=101)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100,101"
        }

    def test_add_to_favourite_when_user_id_not_set(self):
        favourite = Favourite()
        with pytest.raises(IntegrityError):
            favourite.add_to_favourite(pk=100)

    def test_delete_from_favourite(self, favourite):
        favourite.delete_from_favourite(pk=100)

        ids = [100, 101, 102, 103]
        for _id in ids:
            favourite.add_to_favourite(pk=_id)
        favourite.save()

        favourite.delete_from_favourite(pk=101)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100,102,103"
        }

        favourite.delete_from_favourite(pk=100)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "102,103"
        }

        favourite.delete_from_favourite(pk=103)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "102"
        }

        favourite.delete_from_favourite(pk=102)
        favourite.save()

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": ""
        }

    def test_get_fav_id_when_user_id_exists(self, favourite):
        ids = [100, 101, 102, 103]
        for _id in ids:
            favourite.add_to_favourite(pk=_id)
        favourite.save()

        assert favourite.get_favourite_ids(user_id=1) == ids

    def test_get_fav_id_when_user_id_not_exists(self, favourite):
        with pytest.raises(ValueError):
            favourite.get_favourite_ids(user_id=2)

    def test_create_or_update_with_list_of_advert_ids(self):
        ids = [100, 101, 102, 103]
        Favourite.create_or_update(user_id=1, adverts=ids)

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100,101,102,103"
        }

    def test_create_or_update_with_queryset_of_adverts(self, add_testing_data_to_db):
        adverts = Advert.objects.all()
        Favourite.create_or_update(user_id=1, adverts=adverts)

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "1,2"
        }

    def test_create_or_update_with_empty_list(self):
        Favourite.create_or_update(user_id=1, adverts=[])

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": ""
        }

    def test_create_or_update_with_empty_queryset(self):
        empty_queryset = Advert.objects.none()
        Favourite.create_or_update(user_id=1, adverts=empty_queryset)

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": ""
        }

    def test_create_or_update_when_update(self):
        Favourite.create_or_update(user_id=1, adverts=[100])

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100"
        }

        Favourite.create_or_update(user_id=1, adverts=[101])

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "100,101"
        }

    def test_remove_from_favourite_when_ids_in_favourite(self):
        ids = [100, 101, 102, 103]
        Favourite.create_or_update(user_id=1, adverts=ids)

        Favourite.remove_from_favourite(user_id=1, adverts=[100, 103])

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": "101,102"
        }

    def test_remove_from_favourite_when_ids_not_in_favourite(self):
        Favourite.create_or_update(user_id=1, adverts=[])

        Favourite.remove_from_favourite(user_id=1, adverts=[100, 103])

        assert Favourite.objects.values("user_id", "favourite")[0] == {
            "user_id": 1,
            "favourite": ""
        }

    def test_remove_from_favourite_when_user_does_not_exists(self):
        Favourite.remove_from_favourite(user_id=2, adverts=[100])
        assert not Favourite.objects.exists()
