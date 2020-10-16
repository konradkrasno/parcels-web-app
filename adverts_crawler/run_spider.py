import os
import glob
import logging
import requests
import re

from scrapy.utils.project import get_project_settings
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


if __name__ == "__main__":
    [os.remove(file) for file in glob.glob("./scraped_data/*.csv")]

    s = get_project_settings()
    s["FEED_FORMAT"] = "csv"
    s["FEED_URI"] = "scraped_data/adverts.csv"
    process = CrawlerProcess(s)
    process.crawl(MorizonSpider)
    process.crawl(AdresowoSpider)
    process.crawl(StrzelczykSpider)
    process.start()

    # make post request to django service for uploading data to database
    URL = "http://{}:8000/upload_data".format(host)
    requests.post(URL)
