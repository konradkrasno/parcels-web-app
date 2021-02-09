import glob

import pytest
from scrapy.crawler import CrawlerProcess

from parcels import tasks
from parcels.models import Advert
from parcels_web_app.settings import SCRAPED_DATA_CATALOG


@pytest.mark.django_db
def test_run_spider(mocker):
    mocker.patch("glob.glob")
    mocker.patch.object(CrawlerProcess, "crawl", return_value=True)
    mocker.patch.object(CrawlerProcess, "start", return_value=True)
    mocker.patch("parcels.tasks.upload_data")
    process = CrawlerProcess()
    tasks.run_spider()
    glob.glob.assert_called_with(f"{SCRAPED_DATA_CATALOG}/*.csv")
    process.crawl.assert_called()
    process.start.assert_called_once()
    tasks.upload_data.assert_called_once()


@pytest.mark.django_db
def test_upload_data(mocker):
    mocker.patch("parcels.models.Advert.load_adverts")
    mocker.patch("parcels.models.Advert.delete_duplicates")
    tasks.upload_data()
    Advert.load_adverts.assert_called_with(SCRAPED_DATA_CATALOG)
    Advert.delete_duplicates.assert_called_once()
