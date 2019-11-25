import json
import logging
from urllib.parse import urlencode

import scrapy

from quotesbot.spiders.utils.http import JSONRequest

from pprint import pprint

logger = logging.getLogger(__name__)


class ScheduleParser(object):
    def __init__(self, url):
        self.logger = logger
        self.url = url

    def get_start_request(self):
        return scrapy.Request(self.url, callback=self.parse_schedule_page)

    def parse_schedule_page(self, response):
        self.logger.info(f"Event schedules: {response.status}")

        ok = (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return None
        try:
            yield self.extract_schedule_page(response)
        except Exception as e:
            self.logger.error(f"Failed to parse {response.url}")
            content = response.body[:10240]
            if len(response.body) > len(content):
                self.logger.error(f"Response content: {content}... (truncated)")
            else:
                self.logger.error(f"Response content: {content}")

            self.logger.exception(e)
            return None


    @staticmethod
    def extract_schedule_page(response):
        data = json.loads(response.body)
        events = data['data']['prods']
        for event in events:
            event_perfs = event['perfs']
            for ep in event_perfs:
                buy_url = f"https://www.mydso.com/h/syos/SyosSummary?houseid=meyerson&id={ep['id']}&type=perf"
                event_name = event['title'].replace("\xa0", " & ")
                ev = EventParser(event_name, ep['id'], buy_url, ep['date'])
                print(ev)
                yield ev.get_start_request()


class EventParser(object):

    def __init__(self,name, performance_id, buy_url, startDateTimeAsString):

        self.event = {
            "name": name,
            "externalId": performance_id,
            "timezone": 'CST',
            "startDateTimeAsString": startDateTimeAsString,
            "buy_url": buy_url
        }
        self.venue = {
            'name': 'Morton H. Meyerson Symphony Center',
            'cityName': 'Dallas',
            'addressLine1': '2301 Flora St',
            'stateCode': '75201',
            'stateName': 'Texas',
            'countryCode': 'USA',
            'countryName': 'USA'
        }
    def __str__(self):
        return f"{self.event}"
    def get_start_request(self):

        query_params = {'performanceId': self.event['externalId']}
        url = f"https://tickets.nashvillesymphony.org/api/syos/GetPerformanceDetails?{urlencode(query_params)}"
        return JSONRequest(url=url, method="GET", callback=self.parse_performance_info)
#
#     def parse_performance_info(self, response):
#
#         performance_id = self.event['externalId']
#         performance_data = self.get_data(response, f"Received performance response for {performance_id}")
#         product_number = performance_data['prod_no']
#         self.event["description"] = performance_data["description"]
#         self.event['startDateTimeAsString'] = performance_data['perf_dt']
#         self.event['startDateTime'] = parse(performance_data['perf_dt']).strftime("%Y-%m-%dT%H:%M:00.000-05:00")
#         self.event["seatmapUrl"] = f"https://tickets.nashvillesymphony.org/{product_number}/{performance_id}"
#         self.venue['description'] = performance_data.get('facility_desc')
#         self.venue['externalId'] = performance_data['facility_no']
#
#         query_params = {'performanceId': performance_id}
#         screens_url = f"https://tickets.nashvillesymphony.org/api/syos/GetScreens?{urlencode(query_params)}"
#         yield JSONRequest(url=screens_url, method="GET", callback=self.parse_all_screens_info)
#
#     def parse_all_screens_info(self, response):
#
#         screens = self.get_data(response, f"Received screens response for {self.event['externalId']}")
#         self.logger.info(f"Received {len(screens)} screen in total")
#         for screen in screens:
#             query_params = {
#                 'performanceId': self.event['externalId'],
#                 'facilityId': self.venue["externalId"],
#                 'screenId': screen["screen_no"]
#             }
#             screen_url = f"https://tickets.nashvillesymphony.org/api/syos/GetSeatList?{urlencode(query_params)}"
#             yield JSONRequest(url=screen_url, method="GET", callback=self.parse_screen_info,
#                               meta={'section': screen["screen_desc"]})
#
#     def parse_screen_info(self, response):
#
#         section = response.meta.get('section')
#         msg = f"Received screen response for performance {self.event['externalId']} screen {section}"
#         screen_info = self.get_data(response, msg)
#         seats = screen_info.get('seats')
#         available_prices = {price['ZoneNo']: price['Price'] for price in screen_info.get('AvailablePrices')}
#
#         tickets = {}
#         existing_seats = [seat for seat in seats if seat["zone_no"] > 0]
#         for seat in existing_seats:
#             zone = seat["ZoneLabel"]
#             zone_id = seat["zone_no"]
#             if zone_id not in tickets:
#                 tickets[zone_id] = {
#                     "totalSeats": 0, "availableSeats": 0, "section": section,
#                     "subsection": zone, "priceAreaId": zone_id, "price": available_prices.get(zone_id),
#                     "currency": 'USD', "stockEtickets": True, "priceAreaDescription": zone_id}
#             tickets[zone_id]['totalSeats'] += 1
#
#             is_seat_available = seat['seat_status_desc'] == 'Available'
#             if is_seat_available:
#                 tickets[zone_id]['availableSeats'] += 1
#         # data to be sent to server
#         pprint({
#             "backend": "https://www.nashvillesymphony.org/tickets/",
#             'event': self.event,
#             'venue': self.venue,
#             'tickets': list(tickets.values()),
#         })
#         return {
#             "backend": "https://www.nashvillesymphony.org/tickets/",
#             'event': self.event,
#             'venue': self.venue,
#             'tickets': list(tickets.values()),
#         }
#
    # def get_data(self, response, msg, ok=None):
    #     self.logger.info(f"{msg}: {response.status}")
    #
    #     ok = ok or (200, 201)
    #     if response.status not in ok:
    #         self.logger.error(f"Request to {response.url} failed, existing")
    #         return
    #
    #     return json.loads(response.body)
