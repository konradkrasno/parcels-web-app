import os

import pandas as pd
import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory

from ..models import Advert, Favourite
from ..tests.test_data import testing_data

TEST_DIR = "fixtures"


@pytest.fixture
def create_test_csv():
    """ Creates test csv file for testing loading data from file to database. """

    try:
        os.mkdir(os.path.join(os.getcwd(), TEST_DIR))
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
        os.path.join(os.getcwd(), TEST_DIR, "test_data.csv"),
        index=False,
    )


@pytest.fixture
def add_testing_data_to_db():
    """Adds data to database."""

    for item in testing_data:
        Advert(**item).save()
    Advert.delete_duplicates()


@pytest.fixture
def test_adverts(add_testing_data_to_db) -> list:
    return Advert.objects.all()


@pytest.fixture
def user():
    """ Provides fake user. """

    user = User.objects.create(username="test_user", email="test@gmail.com")
    user.set_password("password")
    user.save()
    user = User.objects.get(username="test_user")
    return user


@pytest.fixture
def add_favourites(user, test_adverts):
    Favourite.add_to_favourite(user_id=user.id, adverts=test_adverts)


@pytest.fixture
def client():
    """ Provides fake client. """

    client = Client()
    # if user fixture is used then client log in, otherwise not log in
    client.login(username="test_user", password="password")
    return client


@pytest.fixture
def factory():
    """ Creates fake request. """
    return RequestFactory()
