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

    def prtFunction(self):
        print(
            f"{self.Venue} {self.VenueCity} {self.VenueAddress} {self.VenueState} {self.stateName} {self.VenueCountry} {self.countryName}")

class Event:
    def __init__(self, EventID, Event, PerformanceName, Description='', PerformanceDateTime='', TimeZone='', SeatMapUrl='',
               DisplayIcon=''):
        self.EventID = EventID
        self.Event = Event
        self.PerformanceName = PerformanceName
        self.Description = Description
        self.PerformanceDateTime = PerformanceDateTime
        self.TimeZone = TimeZone
        self.SeatMapUrl = SeatMapUrl
        self.DisplayIcon = DisplayIcon

    def prtFunction(self):
        print(f"{self.EventID} {self.Event} {self.PerformanceName} {self.Description} {self.PerformanceDateTime} {self.TimeZone} {self.SeatMapUrl} {self.DisplayIcon}")

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
        #self.logger.info(f"Event schedules: {response.status}")

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

    def get_data(self, response, msg, ok=None):
        self.logger.info(f"{msg}: {response.status}")

        ok = ok or (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return

        return json.loads(response.body)

    def splitStateCountryName(self, text, index):
        initial_list = text.split('|')

        print('++++++++++++++++++++++\n')
        return(initial_list[index])

    def extract_schedule_page(self, response):
        print('Parsing events page !!!!!!!!!!!!!!!!!\n')
        res = self.get_data(response, 'finished parsing events')
        events = res["performance"]
        list_of_events = []
        list_of_venues = []
        with open("events.txt", "w") as fout:
            for event in events:
                fout.write('\n------------\n')
                fout.write(str(event))
                seat_url = f"https://statetheatre.showare.com/include/modules/SeatingChart/Request/getPerformanceSeatmap.asp?p={event['PerformanceID']}"
                e1 = Event(event['EventID'], event['Event'], event['PerformanceName'], event['Description'], event['PerformanceDateTime'], event['TimeZone'], seat_url, event['DisplayIcon'])
                list_of_events.append(e1)


                initial_list = event['VenueLocation']
                stateName = self.splitStateCountryName(initial_list,2)
                countryName = self.splitStateCountryName(initial_list, 4)

                v1 = Venue(event['Venue'], event['VenueCity'], event['VenueAddress'], event['VenueState'], stateName, event['VenueCountry'], countryName)
                list_of_venues.append(v1)
                yield JSONRequest(url=seat_url, method="GET", callback=self.parse_performance_seatmap)

        # delete the for loop below
        i = 1;
        for event in list_of_events:
            print(i)
            i = i + 1
            event.prtFunction()
            print('-------------------------------------------------------')

        i = 1;
        for venue in list_of_venues:
            print(i)
            i = i + 1
            venue.prtFunction()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!')

    def parse_performance_seatmap(self, response):

        performance_data = self.get_data(response, "Received performance response")
        performance_category_list= performance_data["categories"]
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
        performance_price = {cat['id']:cat for cat in performance_category_list}
        # seats(cat_id, seat_id), available_seats(seat_id)
        


        pprint(performance_price)
        print('\n\n')
        print("*************FINAL CATEGORY****************")
        for category in performance_category_list:
            print(category)

        print('\n\n')
        performance_sections_list = performance_data["sections"]


