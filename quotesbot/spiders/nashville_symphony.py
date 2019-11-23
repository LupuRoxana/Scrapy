import logging
import scrapy

from quotesbot.spiders.parse_nashville_symphony.schedule import ScheduleParser

logger = logging.getLogger(__name__)


class QuotesSpider(scrapy.Spider):
    name = "nashville_symphony"

    print('name: ', name)

    def start_requests(self):
        venue_schedules = [
            #
            ScheduleParser("https://www.nashvillesymphony.org/tickets/")
        ]
        for schedule in venue_schedules:
            yield schedule.get_start_request()
