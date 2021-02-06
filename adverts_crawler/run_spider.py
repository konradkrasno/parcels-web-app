import os
import glob

from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from adverts_crawler.spiders.scraper import (
    MorizonSpider,
    AdresowoSpider,
    StrzelczykSpider,
)

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CATALOG = os.path.join(MAIN_DIR, "../scraped_data")


if __name__ == "__main__":
    [os.remove(file) for file in glob.glob("{}/*.csv".format(DATA_CATALOG))]

    s = get_project_settings()
    s["FEED_FORMAT"] = "csv"
    s["FEED_URI"] = "{}/adverts.csv".format(DATA_CATALOG)
    process = CrawlerProcess(s)
    process.crawl(MorizonSpider)
    process.crawl(AdresowoSpider)
    process.crawl(StrzelczykSpider)
    process.start()

    # # make post request to django service for uploading data to database
    # URL = "http://{}:8000/upload_data/{}".format(host, DATA_CATALOG)
    # requests.post(URL)
