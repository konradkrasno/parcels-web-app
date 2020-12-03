import pytest
import os

from django.contrib.auth.models import User
from parcels.models import Advert, Favourite
from parcels.tests.fixtures import (
    create_test_csv,
    add_testing_data_to_db,
    TEST_DIR,
    user,
    test_adverts,
)
from parcels.tests.test_data import testing_data

from django.db.utils import IntegrityError


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

    def test_add_to_favourite(self, user, test_adverts):
        Favourite.add_to_favourite(user_id=1, adverts=test_adverts)
        added_adverts = Favourite.objects.select_related("adverts").values_list(
            "adverts__place", "adverts__price", "adverts__area"
        )
        expected_adverts = test_adverts.values_list("place", "price", "area")
        assert list(added_adverts) == list(expected_adverts)

    def test_remove_from_favourite(self):
        pass

    def test_get_favourites(self):
        pass

    # def test_add_to_favourite_when_user_id_set(self, favourite):
    #     favourite.add_to_favourite(pk=100)
    #     favourite.add_to_favourite(pk=100)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100",
    #     }
    #
    #     favourite.add_to_favourite(pk=101)
    #     favourite.add_to_favourite(pk=101)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100,101",
    #     }
    #
    # def test_add_to_favourite_when_user_id_not_set(self):
    #     favourite = Favourite()
    #     with pytest.raises(IntegrityError):
    #         favourite.add_to_favourite(pk=100)
    #
    # def test_delete_from_favourite(self, favourite):
    #     favourite.delete_from_favourite(pk=100)
    #
    #     ids = [100, 101, 102, 103]
    #     for _id in ids:
    #         favourite.add_to_favourite(pk=_id)
    #     favourite.save()
    #
    #     favourite.delete_from_favourite(pk=101)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100,102,103",
    #     }
    #
    #     favourite.delete_from_favourite(pk=100)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "102,103",
    #     }
    #
    #     favourite.delete_from_favourite(pk=103)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "102",
    #     }
    #
    #     favourite.delete_from_favourite(pk=102)
    #     favourite.save()
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "",
    #     }
    #
    # def test_get_fav_id_when_user_id_exists(self, favourite):
    #     ids = [100, 101, 102, 103]
    #     for _id in ids:
    #         favourite.add_to_favourite(pk=_id)
    #     favourite.save()
    #
    #     assert favourite.get_favourite_ids(user_id=1) == ids
    #
    # def test_get_fav_id_when_user_id_not_exists(self, favourite):
    #     assert favourite.get_favourite_ids(user_id=2) == []
    #
    # def test_create_or_update_with_list_of_advert_ids(self):
    #     ids = [100, 101, 102, 103]
    #     Favourite.create_or_update(user_id=1, adverts=ids)
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100,101,102,103",
    #     }
    #
    # def test_create_or_update_with_queryset_of_adverts(self, add_testing_data_to_db):
    #     adverts = Advert.objects.all()
    #     Favourite.create_or_update(user_id=1, adverts=adverts)
    #
    #     assert len(Favourite.get_favourite_ids(user_id=1)) == 2
    #
    # def test_create_or_update_with_empty_list(self):
    #     Favourite.create_or_update(user_id=1, adverts=[])
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "",
    #     }
    #
    # def test_create_or_update_with_empty_queryset(self):
    #     empty_queryset = Advert.objects.none()
    #     Favourite.create_or_update(user_id=1, adverts=empty_queryset)
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "",
    #     }
    #
    # def test_create_or_update_when_update(self):
    #     Favourite.create_or_update(user_id=1, adverts=[100])
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100",
    #     }
    #
    #     Favourite.create_or_update(user_id=1, adverts=[101])
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "100,101",
    #     }
    #
    # def test_remove_from_favourite_when_ids_in_favourite(self):
    #     ids = [100, 101, 102, 103]
    #     Favourite.create_or_update(user_id=1, adverts=ids)
    #
    #     Favourite.remove_from_favourite(user_id=1, adverts=[100, 103])
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "101,102",
    #     }
    #
    # def test_remove_from_favourite_when_ids_not_in_favourite(self):
    #     Favourite.create_or_update(user_id=1, adverts=[])
    #
    #     Favourite.remove_from_favourite(user_id=1, adverts=[100, 103])
    #
    #     assert Favourite.objects.values("user_id", "favourite")[0] == {
    #         "user_id": 1,
    #         "favourite": "",
    #     }
    #
    # def test_remove_from_favourite_when_user_does_not_exists(self):
    #     Favourite.remove_from_favourite(user_id=2, adverts=[100])
    #     assert not Favourite.objects.exists()
