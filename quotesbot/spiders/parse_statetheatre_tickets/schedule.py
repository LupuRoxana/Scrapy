import logging
import scrapy
import json
from quotesbot.spiders.utils.http import JSONRequest
from scrapy.utils.response import open_in_browser
from pprint import pprint

logger = logging.getLogger(__name__)


class Venue(object):
    def __init__(self, Venue, VenueCity, VenueAddress, VenueState, stateName, VenueCountry, countryName):
        self.Venue = Venue
        self.VenueCity = VenueCity
        self.VenueAddress = VenueAddress
        self.VenueState = VenueState
        self.stateName = stateName
        self.VenueCountry = VenueCountry
        self.countryName = countryName

    def __str__(self):
        return f"{self.Venue} {self.VenueCity} {self.VenueAddress} {self.VenueState} {self.stateName} {self.VenueCountry} {self.countryName}"


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

    def parse(self, response):
        print('response: ', response)
        open_in_browser(response)
        return self.parse_url(response.url)

    def parse_schedule_page(self, response):
        print('******** parsing schedule page!!!!!!')
        # self.logger.info(f"Event schedules: {response.status}")

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

    def splitStateCountryName(self, text, index):
        initial_list = text.split('|')
        return (initial_list[index])

    def extract_schedule_page(self, response):
        print('Parsing events page !!!!!!!!!!!!!!!!!\n')
        res = self.get_data(response, 'finished parsing events')
        events = res["performance"]
        for event in events:
            ev = Event(event['EventID'], event['Event'], event['PerformanceID'], event['PerformanceName'],
                       event['Description'], event['PerformanceDateTime'], event['TimeZone'], event['DisplayIcon'])
            initial_list = event['VenueLocation']
            stateName = self.splitStateCountryName(initial_list, 2)
            countryName = self.splitStateCountryName(initial_list, 4)

            ev.venue = Venue(event['Venue'], event['VenueCity'], event['VenueAddress'], event['VenueState'], stateName,
                             event['VenueCountry'], countryName)
            yield ev.start_request()

    def get_data(self, response, msg, ok=None):
        self.logger.info(f"{msg}: {response.status}")

        ok = ok or (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return

        return json.loads(response.body)


class Event:
    def __init__(self, EventID, Event, PerformanceId, PerformanceName, Description='', PerformanceDateTime='',
                 TimeZone='',
                 DisplayIcon=''):
        self.EventID = EventID
        self.Event = Event
        self.PerformanceId = PerformanceId
        self.PerformanceName = PerformanceName
        self.Description = Description
        self.PerformanceDateTime = PerformanceDateTime
        self.TimeZone = TimeZone
        self.SeatMapUrl = f"https://statetheatre.showare.com/orderticketsvenue.asp?p={self.PerformanceId}"
        self.DisplayIcon = DisplayIcon
        self.logger = logger



    def __str__(self):
        return f"{self.EventID} {self.Event} {self.PerformanceName} {self.Description} {self.PerformanceDateTime} {self.TimeZone} {self.SeatMapUrl} {self.DisplayIcon}"

    def start_request(self):
        seat_url = f"https://statetheatre.showare.com/include/modules/SeatingChart/Request/getPerformanceSeatmap.asp?p={self.PerformanceId}"
        return JSONRequest(url=seat_url, method="GET", callback=self.parse_performance_seatmap)

    def parse_performance_seatmap(self, response):
        performance_data = self.get_data(response, "Received performance response")
        performance_category_list = performance_data["categories"]
        print("*************CATEGORY****************")
        print(performance_category_list)
        print('\n\n')
        print("*************PRICE****************")
        performance_price_list = performance_data["prices"]
        print(performance_price_list)
        print('\n\n')
        for category in performance_category_list:
            for price in performance_price_list:
                if category['id'] == price['seatCategory']:
                    category['price'] = price['price']
                    category.pop('color')
        self.performance_price_dict = {str(cat['id']): cat for cat in performance_category_list}
        # seats(cat_id, seat_id), available_seats(seat_id)
        url = f"https://statetheatre.showare.com/include/modules/SeatingChart/request/getPerformanceSeats.asp?p={self.PerformanceId}"
        print(url)
        yield JSONRequest(url, method="GET", callback=self.parse_performance_seats)

    def parse_performance_seats(self, response):
        total_tickets = []
        self.seats_data = self.get_data(response, "Received seats response")
        print(self.venue)
        url = f"https://statetheatre.showare.com/include/modules/SeatingChart/request/getPerformanceAvailability.asp?p={self.PerformanceId}"
        print(url)


        yield JSONRequest(url, method="GET", callback=self.parse_performance_seats_availability)

    def parse_performance_seats_availability(self, response):
        seats_availability = self.get_data(response, 'Received seats availability response')

        print("----------------------")
        seats_availability_list = []
        for seats_av in seats_availability:
            seats_availability_list.append(self.splitStateCountryName(seats_av, 0))
        pprint(seats_availability_list)
        for seat in self.seats_data:
            id_seat = self.splitStateCountryName(seat,0)
            id_category = self.splitStateCountryName(seat, 4)
            if 'total' not in self.performance_price_dict[id_category]:
                self.performance_price_dict[id_category]['total'] = 0
                self.performance_price_dict[id_category]['available'] = 0
            self.performance_price_dict[id_category]['total'] += 1
            if id_seat in seats_availability_list:
                self.performance_price_dict[id_category]['available'] += 1

        print("\n\n----------------------")
        pprint(self.performance_price_dict)



    def get_data(self, response, msg, ok=None):
        self.logger.info(f"{msg}: {response.status}")

        ok = ok or (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return

        return json.loads(response.body)

    def splitStateCountryName(self, text, index):
        initial_list = text.split('|')
        return (initial_list[index])