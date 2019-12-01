import logging
import scrapy

from quotesbot.spiders.parse_kimmelcenter.schedule import ScheduleParser

logger = logging.getLogger(__name__)


class QuotesSpider(scrapy.Spider):
    name = "kimmelcenter"

    print('name: ', name)

    def start_requests(self):
        venue_schedules = [
            ScheduleParser("https://www.kimmelcenter.org/api/calendar/GetUpcomingEventsByTitle")
        ]
        for schedule in venue_schedules:
            yield schedule.get_start_request()