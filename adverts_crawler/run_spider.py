import logging
import requests
import os
import re

from scrapy.crawler import CrawlerProcess
from adverts_crawler.spiders.scraper import (
    MorizonSpider,
    AdresowoSpider,
    StrzelczykSpider,
)


MAIN_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
    )
)

HOSTS_DIR = os.path.join(MAIN_DIR, "etc/hosts")

try:
    with open(HOSTS_DIR) as f:
        host = re.match(r"([0-9]*(\.))*", list(f).pop()).group() + "1"
except FileNotFoundError:
    host = "127.0.0.1"

logging.info("Host: {}".format(host))


if "adverts.json" in os.listdir("."):
    os.remove("adverts.json")

process = CrawlerProcess(settings={"FEED_FORMAT": "json", "FEED_URI": "adverts.json"})


if __name__ == "__main__":
    process.crawl(MorizonSpider)
    process.start()

    # make post request to django service for uploading data to database
    URL = "http://{}:8000/upload_data".format(host)
    requests.post(URL)
