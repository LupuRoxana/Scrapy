import logging
import scrapy

from quotesbot.spiders.parse_statetheatre_tickets.schedule import ScheduleParser

logger = logging.getLogger(__name__)


class QuotesSpider(scrapy.Spider):
    name = "statetheatre_tickets"

    print('name: ', name)

    def start_requests(self):
        venue_schedules = [
            #
            ScheduleParser("https://statetheatre.showare.com/include/widgets/events/performancelist.asp?fromDate=&toDate=&venue=0&city=&swEvent=0&category=0&searchString=&searchType=0&showHidden=0&showPackages=1&action=perf&listPageSize=1000&listMaxSize=100&page=1")
        ]
        for schedule in venue_schedules:
            yield schedule.get_start_request()
