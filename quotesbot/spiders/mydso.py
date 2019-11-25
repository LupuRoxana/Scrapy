import logging
import scrapy

from quotesbot.spiders.parse_mydso.schedule import ScheduleParser

logger = logging.getLogger(__name__)


class QuotesSpider(scrapy.Spider):
    name = "mydso"

    print('name: ', name)

    def start_requests(self):
        venue_schedules = [
            #
            ScheduleParser("https://www.mydso.com/h/productions/BuyTicketsBarData")
        ]
        for schedule in venue_schedules:
            yield schedule.get_start_request()