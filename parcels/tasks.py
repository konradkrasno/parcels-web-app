import glob
import logging
import os
from typing import *

from celery import shared_task
from django.core.mail import EmailMessage
from django.db.utils import ProgrammingError
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from adverts_crawler.adverts_crawler.spiders.scraper import (
    MorizonSpider,
    AdresowoSpider,
    StrzelczykSpider,
)
from parcels.models import Advert
from parcels_web_app.settings import SCRAPED_DATA_CATALOG

logging.basicConfig(level=logging.DEBUG)


@shared_task
def send_email(subject: str, body: str, to: List, attachments: List = None) -> None:
    email = EmailMessage(subject=subject, body=body, to=to, attachments=attachments)
    email.send()


@shared_task
def run_spider() -> None:
    # remove files
    [os.remove(file) for file in glob.glob(f"{SCRAPED_DATA_CATALOG}/*.csv")]

    # crawl data
    s = get_project_settings()
    s["FEED_FORMAT"] = "csv"
    s["FEED_URI"] = f"{SCRAPED_DATA_CATALOG}/adverts.csv"
    process = CrawlerProcess(s)
    process.crawl(MorizonSpider)
    process.crawl(AdresowoSpider)
    process.crawl(StrzelczykSpider)
    process.start()
    logging.info("Data scraped successfully")

    # Upload data to db
    upload_data()


@shared_task
def upload_data() -> None:
    try:
        Advert.load_adverts(SCRAPED_DATA_CATALOG)
    except (ProgrammingError, FileNotFoundError) as e:
        logging.error(f"ERROR: {e.__str__()}")
    Advert.delete_duplicates()
    logging.info("Data successfully updated.")
