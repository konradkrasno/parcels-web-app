import glob
import os
from typing import *

import requests
from celery import shared_task
from django.core.mail import EmailMessage
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from adverts_crawler.adverts_crawler.spiders.scraper import (
    MorizonSpider,
    AdresowoSpider,
    StrzelczykSpider,
)
from parcels_web_app.settings import SCRAPED_DATA_CATALOG, WEB_HOST


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

    # make post request to django service for uploading data to database
    URL = f"http://{WEB_HOST}:8000/upload_data"
    requests.post(URL)
