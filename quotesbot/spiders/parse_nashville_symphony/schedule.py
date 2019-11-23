# import js2py
import logging
import scrapy
import json

from quotesbot.spiders.utils.http import JSONRequest
from scrapy.utils.response import open_in_browser
# from scrapy.http import JSONRequest

from datetime import datetime
# from scrapy_splash import SplashRequest, SplashFormRequest

# from ticketbash_spider.utils import (
#     convert_javascript_to_python,
#     dev,
#     make_url,
#     parse_javascript_callsite,
# )
# from ticketbash_spider.spiders.audienceview.seatmap import SeatMapParser

logger = logging.getLogger(__name__)


class ScheduleParser(object):
    def __init__(self, url):
        self.logger = logger
        self.url = url

    def get_start_request(self):
        print('Making request for url ', self.url)
        # Make the request to receive the cookie (https://stackoverflow.com/questions/34707532/python-post-request-not-returning-html-requesting-javascript-be-enabled/38082203)
        lua_script = """
        function main(splash)
        local url = splash.args.url
        assert(splash:go(url))
        assert(splash:wait(2))
        return {
            html = splash:html(),
            cookies = splash:get_cookies(),
        }
        end
        """
        return scrapy.Request(self.url, callback=self.parse_schedule_page)
        # return SplashRequest(
        #     self.url,
        #     self.parse,
        #     endpoint="execute",
        #     args={"wait": 1, "lua_source": lua_script},
        # )

    def parse(self, response):
        print('response: ', response)
        open_in_browser(response)
        return self.parse_url(response.url)

    def parse_url(self, url):
        # Perform the request with the cookie
        lua_script = """
        function main(splash)
        splash:init_cookies(splash.args.cookies)
        local url = splash.args.url
        assert(splash:go(url))
        assert(splash:wait(2))
        return {
            html = splash:html(),
        }
        end
        """
        return SplashRequest(
            url,
            self.parse_schedule_page,
            endpoint="execute",
            args={"wait": 1, "lua_source": lua_script},
            dont_filter=True,
        )

    def parse_schedule_page(self, response):
        print('******** parsing schedule page!!!!!!')
        self.logger.info(f"Event schedules: {response.status}")

        ok = (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return None

        print('will extract schedule pageß')

        try:
            # for schedule_result in self.extract_schedule_page(response):
            #     yield schedule_result
            yield next(self.extract_schedule_page(response))
        except Exception as e:
            self.logger.error(f"Failed to parse {response.url}")
            content = response.body[:10240]
            if len(response.body) > len(content):
                self.logger.error(f"Response content: {content}... (truncated)")
            else:
                self.logger.error(f"Response content: {content}")

            self.logger.exception(e)
            return None

    def extract_schedule_page(self, response):

        print('Parsing events page !!!!!!!!!!!!!!!!!\n\n\n\n\n')

        events = response.css("#eventList .event")
        logger.info(f"✅ Discovered {len(events.getall())} events")

        for index, event in enumerate(events):
            print('====================================')
            print('Event number ', index)
            print('Name: ', event.css('h3::text').get())
            print('Venue: ', event.css('h5::text').get())
            tics = event.css('.tic-quad>.tic')
            print(f"The event has {len(tics.getall())} dates")
            # tic is actually a performance
            for tic in tics[1:2]:
                print('Date: ', tic.css('.date::text').get())
                print('Day: ', tic.css('.day::text').get())
                print('Time: ', tic.css('.day>span::text').get())
                buy_url = tic.css('a::attr(href)').get();
                performance_id = buy_url.partition('.aspx?p=')[2]
                print('performance id: ', performance_id)
                print('Url to buy the ticket: ', buy_url)
                tic_url = f"https://tickets.nashvillesymphony.org/api/syos/GetPerformanceDetails?performanceId={performance_id}"
                yield JSONRequest(url=tic_url, method="GET", callback=self.parse_performance_info)

    def parse_performance_info(self, response):

        performance_data = self.get_data(response, "Received performance response")
        performance_id = performance_data["perf_no"]
        description = performance_data["description"]
        print('Parsing performance info for ', performance_id)
        screens_url = f"https://tickets.nashvillesymphony.org/api/syos/GetScreens?performanceId={performance_id}"
        self.logger.info(f"TicketInfo for {description}")
        yield JSONRequest(url=screens_url, method="GET", callback=self.parse_all_screens_info, meta={"performance_data": performance_data})

    def parse_all_screens_info(self, response):

        screens = self.get_data(response, "Received screens response")
        performance_data = response.meta.get("performance_data")
        performance_id = performance_data["perf_no"]
        facility_id = performance_data["facility_no"]
        # print('=========================== screen data')
        # print(screen_data)
        # print('===========================')
        for screen in screens[1:2]:
            screen_no = screen["screen_no"]
            screen_url = f"https://tickets.nashvillesymphony.org/api/syos/GetSeatList?performanceId={performance_id}&facilityId={facility_id}&screenId={screen_no}"
            yield JSONRequest(url=screen_url, method="GET", callback=self.parse_screen_info)

    def parse_screen_info(self, response):
        screen_info = self.get_data(response, 'Received screen response')
        seats = screen_info.get('seats')
        # print('seats: ', seats)
        d = {}
        for seat in seats:
            zone = seat["ZoneLabel"]
            isAvailable = seat['seat_status_desc'] == 'Available'
            if zone not in d:
                d[zone] = {"total": 0, "available": 0}
            d[zone]['total'] += 1
            if isAvailable:
                d[zone]['available'] += 1
        print('group by zone and count available and total: ', d)
        # -[RECORD 1] - ---------+---------------------------
        # id | 1
        # row |
        # section | Orchestra
        # startSeatNumber |
        # endSeatNumber |
        # availableSeats | 59
        # inventoryType | primary
        # currency | USD
        # price | 129
        # priceOfferName |
        # priceAreaDescription | Premium
        # createdAt | 2019 - 11 - 11
        # 21: 58:39.935 + 02
        # updatedAt | 2019 - 11 - 11
        # 21: 58:39.935 + 02
        # eventId | 1
        # totalSeats | 345
        # originData |
        # stockEtickets | f
        # stockFlash | f
        # stockHard | f
        # stockMobileQR | f
        # stockMobileTransfer | f
        # stockPaperlessGiftCard | f
        # stockPaperlessWalkIn | f

    def get_data(self, response, msg, ok=None):
        self.logger.info(f"{msg}: {response.status}")

        ok = ok or (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return

        return json.loads(response.body)
