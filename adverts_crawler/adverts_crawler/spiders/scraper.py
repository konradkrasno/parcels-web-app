import scrapy
import re


def remove_tags(text):
    tag_re = re.compile(r"<[^>]+>")
    return tag_re.sub("", text)


class MorizonSpider(scrapy.Spider):
    name = "morizon"

    def start_requests(self):

        for i in range(1, 35):
            if i == 1:
                yield scrapy.Request(
                    "https://www.morizon.pl/dzialki/budowlana/minski",
                    callback=self.parse_advert,
                )
            else:
                yield scrapy.Request(
                    "https://www.morizon.pl/dzialki/budowlana/minski/?page=" + str(i),
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
            .split(",")[0],
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
        }

        yield data


class AdresowoSpider(scrapy.Spider):
    name = "adresowo"

    def start_requests(self):

        for i in range(1, 13):
            if i == 1:
                yield scrapy.Request(
                    "https://adresowo.pl/dzialki/powiat-minski/fz1z4",
                    callback=self.parse_advert,
                )
            else:
                yield scrapy.Request(
                    "https://adresowo.pl/dzialki/powiat-minski/fz1z4_l" + str(i),
                    callback=self.parse_advert,
                )

    def parse_advert(self, response):
        pages = response.xpath('//div[@class="result-info"]/a/@href').extract()

        for page in pages:
            url = "https://adresowo.pl" + page
            request = scrapy.Request(url=url, callback=self.parse_advert_data)
            request.meta["link"] = url
            yield request

    @staticmethod
    def parse_advert_data(response):
        data = {
            "place": response.xpath('//span[@class="offer-header__city"]/text()').get(),
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
        }

        yield data


class StrzelczykSpider(scrapy.Spider):
    name = "strzelczyk"

    def start_requests(self):
        for i in range(0, 3):
            yield scrapy.Request(
                "https://www.strzelczyk-nieruchomosci.pl/oferty/?page=" + str(i),
                callback=self.parse_advert,
            )

    def parse_advert(self, response):
        pages = response.xpath(
            '//div[@class="bottomLinkOffer listMore"]/a/@href'
        ).extract()

        for page in pages:
            url = "https://www.strzelczyk-nieruchomosci.pl/" + page
            request = scrapy.Request(url=url, callback=self.parse_advert_data)
            request.meta["link"] = url
            yield request

    @staticmethod
    def parse_advert_data(response):
        data = {
            "place": response.xpath('//div[@class="locationOffer"]/text()')
            .get()
            .split(", ")[1],
            "county": response.xpath('//div[@class="locationOffer"]/text()')
            .get()
            .split()[0],
            "price": response.xpath(
                '//div[@class="ofePrice pull-left fieldHeadOfe"]/span/text()'
            )
            .get()
            .replace(" ", "")
            .replace("zł", "")
            .replace(",", "."),
            "price_per_m2": response.xpath(
                '//div[@class="ofePriceSquare pull-left fieldHeadOfe"]/span[2]/text()'
            )
            .get()
            .replace(" ", "")
            .replace(",", "."),
            "area": response.xpath(
                '//div[@class="ofeArea pull-left fieldHeadOfe"]/span[2]/text()'
            )
            .get()
            .replace(" ", "")
            .replace(",", "."),
            "link": response.meta["link"],
            "date_added": "brak danych",
            "description": remove_tags(
                " ".join(
                    response.xpath('//div[@class="valueDescription"]').get().split()
                )
            )
            + "\n"
            + remove_tags(
                " ".join(
                    response.xpath(
                        '//div[@class="col-xs-12 col-sm-12 '
                        "col-md-6 col-lg-6 noPaddingLeft pu"
                        'll-right"]'
                    )
                    .get()
                    .split()
                )
            ),
        }

        yield data
