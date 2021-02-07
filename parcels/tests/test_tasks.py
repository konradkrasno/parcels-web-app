import pytest

from parcels import tasks
from parcels.models import Advert
from parcels_web_app.settings import SCRAPED_DATA_CATALOG
from scrapy.crawler import CrawlerProcess
import glob


@pytest.mark.django_db
def test_run_spider(mocker):
    mocker.patch("glob.glob")
    process = CrawlerProcess()
    spy_crawl = mocker.spy(process, "crawl")
    spy_start = mocker.spy(process, "start")
    mocker.patch("parcels.tasks.upload_data")
    tasks.run_spider("test_spider")
    glob.glob.assert_called_with(f"{SCRAPED_DATA_CATALOG}/*.csv")
    spy_crawl.assert_not_called()
    assert not process.start()
    spy_start.assert_called_once()
    tasks.upload_data.assert_called_once()


@pytest.mark.django_db
def test_upload_data(mocker):
    mocker.patch("parcels.models.Advert.load_adverts")
    mocker.patch("parcels.models.Advert.delete_duplicates")
    tasks.upload_data()
    Advert.load_adverts.assert_called_with(SCRAPED_DATA_CATALOG)
    Advert.delete_duplicates.assert_called_once()
