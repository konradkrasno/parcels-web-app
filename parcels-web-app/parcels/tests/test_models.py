from django.test import TestCase
from unittest.mock import patch, mock_open

import json

from parcels.models import Advert, Favourite
from parcels.tests.test_data import data

# Create your tests here.


class AdvertTests(TestCase):
    def setUp(self):
        Advert.objects.all().delete()

        for item in data:
            advert = Advert(**item)
            advert.save()

        Advert.delete_duplicates()

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps(data))
    def test_download_adverts_from_json(self, mock_file):
        Advert.download_adverts_from_json()
        mock_file.assert_called_with("adverts.json", "r")
        self.assertEqual(
            Advert.objects.values("description")[0]["description"],
            data[0]["description"],
        )

    def test_delete_duplicates(self):
        actual_data = [obj["link"] for obj in Advert.objects.values("link")]
        expected_data = [
            "https://debe-wielkie.nieruchomosci-online.pl/dzialka,na-sprzedaz/21470800.html",
            "https://rysie.nieruchomosci-online.pl/dzialka,na-sprzedaz/20654752.html",
        ]

        self.assertListEqual(actual_data, expected_data)

    def test_filter_adverts(self):
        filtered_adverts_1 = Advert.filter_adverts(
            place="Dębe Wielkie", price=400000, area=800
        ).values("link")
        actual_data_1 = [obj["link"] for obj in filtered_adverts_1]

        expected_data_1 = [
            "https://debe-wielkie.nieruchomosci-online.pl/dzialka,na-sprzedaz/21470800.html"
        ]

        filtered_adverts_2 = Advert.filter_adverts(
            place="Rysie", price=200000, area=1000
        ).values("link")
        actual_data_2 = [obj["link"] for obj in filtered_adverts_2]

        expected_data_2 = [
            "https://rysie.nieruchomosci-online.pl/dzialka,na-sprzedaz/20654752.html"
        ]

        self.assertListEqual(actual_data_1, expected_data_1)
        self.assertListEqual(actual_data_2, expected_data_2)


class FavouriteTests(TestCase):
    def setUp(self):
        Advert.objects.all().delete()

        for item in data:
            advert = Advert(**item)
            advert.save()

    def test_add_to_favourite_first_time(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": "100"}

        self.assertDictEqual(
            Favourite.objects.values("user_id", "favourite")[0], expected_data
        )

    def test_add_to_favourite(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": "100,101"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

        favourite.add_to_favourite(pk=101)
        favourite.save()

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

    def test_delete_from_favourite(self):
        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.add_to_favourite(pk=102)
        favourite.add_to_favourite(pk=103)
        favourite.save()

        favourite.delete_from_favourite(pk=101)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": "100,102,103"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

        favourite.delete_from_favourite(pk=100)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": "102,103"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

        favourite.delete_from_favourite(pk=103)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": "102"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

        favourite.delete_from_favourite(pk=102)
        favourite.save()

        expected_data = {"user_id": 1, "favourite": ""}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

    def test_get_fav_id(self):
        fav_id_1 = Favourite.get_fav_id(user_id=1)
        self.assertEqual(fav_id_1, [])

        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.add_to_favourite(pk=102)
        favourite.add_to_favourite(pk=103)
        favourite.save()

        fav_id_2 = Favourite.get_fav_id(user_id=1)
        self.assertListEqual(fav_id_2, [100, 101, 102, 103])

    def test_make_favourite(self):
        Favourite.make_favourite(pk=100, user_id=1)

        expected_data = {"user_id": 1, "favourite": "100"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

        Favourite.make_favourite(pk=101, user_id=1)
        Favourite.make_favourite(pk=102, user_id=1)
        Favourite.make_favourite(pk=103, user_id=1)

        expected_data = {"user_id": 1, "favourite": "100,101,102,103"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

    def test_make_many_favourite(self):
        actual_adverts_1 = Advert.objects.all()
        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_1)

        expected_data_1 = {"user_id": 1, "favourite": "1,2,3,4,5"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_1,
        )

        for item in data[:2]:
            advert = Advert(**item)
            advert.save()

        actual_adverts_2 = Advert.objects.all()
        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_2)

        expected_data_2 = {"user_id": 1, "favourite": "1,2,3,4,5,6,7"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

    def test_remove_favourite(self):
        Favourite.remove_favourite(pk=100, user_id=1)

        favourite = Favourite()
        favourite.add_to_favourite_first_time(pk=100, user_id=1)
        favourite.add_to_favourite(pk=101)
        favourite.add_to_favourite(pk=102)
        favourite.add_to_favourite(pk=103)
        favourite.save()

        Favourite.remove_favourite(pk=102, user_id=1)

        expected_data = {"user_id": 1, "favourite": "100,101,103"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data,
        )

    def test_remove_many_favourite(self):
        actual_adverts_1 = Advert.objects.all()

        Favourite.remove_many_favourite(user_id=1, adverts=actual_adverts_1)

        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_1)

        expected_data_1 = {"user_id": 1, "favourite": "1,2,3,4,5"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_1,
        )

        for item in data[:2]:
            advert = Advert(**item)
            advert.save()

        actual_adverts_2 = Advert.objects.all()
        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_2)

        expected_data_2 = {"user_id": 1, "favourite": "1,2,3,4,5,6,7"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

        Favourite.remove_many_favourite(user_id=1, adverts=actual_adverts_1)

        expected_data_2 = {"user_id": 1, "favourite": "6,7"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

        Favourite.remove_many_favourite(user_id=1, adverts=actual_adverts_2)

        expected_data_2 = {"user_id": 1, "favourite": ""}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

    def test_remove_many_favourite_from_favourites(self):
        actual_adverts_1 = Advert.objects.all()

        Favourite.remove_many_favourite(user_id=1, adverts=[1, 2])

        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_1)

        expected_data_1 = {"user_id": 1, "favourite": "1,2,3,4,5"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_1,
        )

        for item in data[:2]:
            advert = Advert(**item)
            advert.save()

        actual_adverts_2 = Advert.objects.all()
        Favourite.make_many_favourite(user_id=1, adverts=actual_adverts_2)

        expected_data_2 = {"user_id": 1, "favourite": "1,2,3,4,5,6,7"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

        Favourite.remove_many_favourite(user_id=1, adverts=[1, 2, 3, 4, 5])

        expected_data_2 = {"user_id": 1, "favourite": "6,7"}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )

        Favourite.remove_many_favourite(user_id=1, adverts=[6, 7])

        expected_data_2 = {"user_id": 1, "favourite": ""}

        self.assertDictEqual(
            Favourite.objects.filter(user_id=1).values("user_id", "favourite")[0],
            expected_data_2,
        )
