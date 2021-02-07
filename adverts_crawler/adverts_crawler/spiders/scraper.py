import scrapy
import re


def remove_tags(text):
    tag_re = re.compile(r"<[^>]+>")
    return tag_re.sub("", text)


class MorizonSpider(scrapy.Spider):
    name = "morizon"

    def start_requests(self):
        for i in range(1, 35):
            yield scrapy.Request(
                f"https://www.morizon.pl/dzialki/budowlana/minski/?page={i}",
                callback=self.parse_advert,
            )

    def parse_advert(self, response):
        pages = response.xpath(
            '//a[@class="property_link property-url"]/@href'
        ).extract()
        dates = response.xpath(
            '//span[@class="single-result__category single-result__category--date"]/text()'
        ).extract()
        dates_added = ["".join(date.split()).replace("-", "/") for date in dates]
        data = zip(pages, dates_added)

        for page, date in data:
            request = scrapy.Request(url=page, callback=self.parse_advert_data)
            request.meta["link"] = page
            request.meta["date_added"] = date
            yield request

    @staticmethod
    def parse_advert_data(response):
        data = {
            "place": response.xpath('//div[@class="col-xs-9"]/h1/strong/span[2]/text()')
            .get()
            .split(",")[0]
            .strip(),
            "county": "".join(
                response.xpath('//div[@class="col-xs-9"]/h1/strong/span/text()')
                .get()
                .split()
            )
            .lower()
            .replace(",", ""),
            "price": "".join(
                response.xpath('//li[@class="paramIconPrice"]/em/text()')
                .get()
                .replace(",", ".")
                .split()
            ),
            "price_per_m2": "".join(
                response.xpath('//li[@class="paramIconPriceM2"]/em/text()')
                .get()
                .replace(",", ".")
                .split()
            ),
            "area": "".join(
                response.xpath('//li[@class="paramIconLivingArea"]/em/text()')
                .get()
                .replace(",", ".")
                .split()
            ),
            "link": response.meta["link"],
            "date_added": response.meta["date_added"],
            "description": remove_tags(
                " ".join(response.xpath('//div[@class="description"]').get().split())
            ),
            "image_url": response.xpath('//div[@class="imageBig"]/img/@src').get(),
        }
        yield data


class AdresowoSpider(scrapy.Spider):
    name = "adresowo"

    def start_requests(self):
        for i in range(1, 13):
            yield scrapy.Request(
                f"https://adresowo.pl/dzialki/powiat-minski/fz1z4_l{i}",
                callback=self.parse_advert,
            )

    def parse_advert(self, response):
        pages = response.xpath('//div[@class="result-info"]/a/@href').extract()

        for page in pages:
            url = f"https://adresowo.pl{page}"
            request = scrapy.Request(url=url, callback=self.parse_advert_data)
            request.meta["link"] = url
            yield request

    @staticmethod
    def parse_advert_data(response):
        data = {
            "place": response.xpath('//span[@class="offer-header__city"]/text()')
            .get()
            .strip(),
            "county": "miński",
            "price": response.xpath(
                '//div[@class="offer-summary__item offer-summary__item1"]/div/span/text()'
            )
            .get()
            .replace(" ", "")
            .replace(",", "."),
            "price_per_m2": response.xpath(
                '//div[@class="offer-summary__item offer-summary__item2"]/div/span/text()'
            )
            .get()
            .replace(" ", "")
            .replace(",", "."),
            "area": response.xpath(
                '//div[@class="offer-summary__item offer-summary__item1"]/div[2]/span/text()'
            )
            .get()
            .replace(" ", "")
            .replace(",", "."),
            "link": response.meta["link"],
            "date_added": "brak danych",
            "description": remove_tags(
                " ".join(
                    response.xpath(
                        '//p[@class="offer-description__text offer-'
                        'description__text--drop-cap"]'
                    )
                    .get()
                    .split()
                )
            )
            + "\n"
            + remove_tags(
                " ".join(
                    response.xpath('//ul[@class="offer-description__summary"]')
                    .get()
                    .split()
                )
            ),
            "image_url": response.xpath('//div[@class="offer-gallery"]/img/@src').get(),
        }
        yield data


class StrzelczykSpider(scrapy.Spider):
    name = "strzelczyk"

    def start_requests(self):
        for i in range(0, 3):
            yield scrapy.Request(
                f"https://www.sulejowek-nieruchomosci.pl/oferty/dzialki/sprzedaz/?page={i}",
                callback=self.parse_advert,
            )

    def parse_advert(self, response):
        pages = response.xpath('//div[@class="link-to-offer"]/@data-href').extract()

        for page in pages:
            url = f"https://www.sulejowek-nieruchomosci.pl/{page}"
            request = scrapy.Request(url=url, callback=self.parse_advert_data)
            request.meta["link"] = url
            yield request

    @staticmethod
    def parse_advert_data(response):
        data = {
            "place": response.xpath(
                '//li[@class="breadcrumb-item active"]/a/span/text()'
            )
            .get()
            .strip(),
            "county": "brak danych",
            "price": response.xpath(
                '//div[@class="col-md-3 offer--shortcut__details cena"]/span[@class="offer--shortcut__span-value"]/text()'
            )
            .get()
            .replace(" ", ""),
            "price_per_m2": response.xpath(
                '//div[@class="col-md-3 offer--shortcut__details cena_za"]/span[@class="offer--shortcut__span-value"]/text()'
            )
            .get()
            .split()[0]
            .replace(",", "."),
            "area": "".join(
                response.xpath(
                    '//div[@class="col-md-3 offer--shortcut__details powierzchnia"]/span[@class="offer--shortcut__span-value"]/text()'
                )
                .get()
                .replace(",", ".")
                .replace("m²", "")
                .split()
            ),
            "link": response.meta["link"],
            "date_added": "brak danych",
            "description": remove_tags(
                " ".join(
                    response.xpath('//div[@class="section__text-group"]').get().split()
                )
            ),
            "image_url": response.xpath(
                '//div[@class="image-container"]/a/@href'
            ).get(),
        }
        yield data
