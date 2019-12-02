import json
import logging
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
            for schedule_result in self.extract_schedule_page(response):
                yield schedule_result
            # yield next(self.extract_schedule_page(response))

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
        data = get_data(response,'')
        for dt in data:
            event = dt['performance']
            street_number = event['venueAddress'].split(' ', 1)

            buy_url = f"https://tickets.philorch.org/SmartSeat/Index?itemNumber={event['id']}#/seatmap"
            url = "https://tickets.philorch.org/api/seating/GetSeatmap"

            if url != "https://tickets.philorch.org/api/seating/GetSeatmap":
                proxies = ""
            else:
                proxies = "http://e5a4a23393fd42f6b538816e3f8fb0e9:@proxy.crawlera.com:8010/"
            data = {"itemType":0,
                    "itemId":event['id'],
                    "minPrice":"null",
                    "maxPrice":"null",
                    "allowSeparatedSeats":"false",
                    "priceTypeQuantities":[],
                    "venueLevels":[],
                    "allowAisleAccessSelected":"false",
                    "additionalSeatingOptions":[],
                    "seatMapId":"","language":"null",
                    "seatsToIgnore":[],
                    "isSyosOnly":"false"}
            headers = {"content-type": "application/json"}
            ev = EventParser(event['name'], event['id'], buy_url, event['eventDate'], event['venueName'], street_number[0])
            yield JSONRequest(url, method="POST", headers = headers, data = data, meta= {'proxy': proxies}, callback=ev.parse_performance_seats)





class EventParser(object):

    def __init__(self,name, performance_id, buy_url, startDateTimeAsString, venue_Name, street_number):

        self.logger = logger
        self.event = {
            "name": name,
            "externalId": performance_id,
            "timezone": 'EST',
            "startDateTimeAsString": startDateTimeAsString,
            "buy_url": buy_url

        }
        self.venue = {
            'name': venue_Name,
            'cityName': 'Philadelphia',
            'addressLine1': f"{street_number}{' '}South Broad Street",
            'stateCode': '19102',
            'stateName': 'Pennsylvania',
            'countryCode': 'USA',
            'countryName': 'USA'
        }
    def __str__(self):
        return f"{self.event}"

    def parse_performance_seats(self, response):
        data = get_data(response, 'Message')

        tickets_dict = {}
        all_seats_pricing = data.get('allSeatPricing', [])

        for seats_pricing in all_seats_pricing:
            prices = seats_pricing.get('prices', [])
            for price in prices:
                price_id = price['zoneId']
                if price['zoneId'] not in tickets_dict:
                    tickets_dict[price_id] = {"price":price['price']}
        print('!!!!!!!!!!!!!!!!!')
        # pprint(tickets_dict)

        seats = data.get('levelSeats', [])
        tickets_zones_dict = {}
        for seat in seats:
            is_available = seat['tessituraSeat']['isAvailable']
            zone_id = seat['tessituraSeat']['zoneId']
            id_seat  = seat['seatId']
            section_desc = seat['tessituraSeat']['sectionDescription']
            tickets_zones_dict = {id_seat: {"section" : section_desc, "priceAreaId": zone_id, "curency": "USD", "available": is_available}}

            if zone_id in tickets_dict:
                print("ifffffffffffff")
                tickets_zones_dict[id_seat]['price'] = tickets_zones_dict[zone_id]["price"]
        print('!!!!!!!!!!!!!!!!!')
        pprint(tickets_zones_dict)



        # tickets_zones_dict = {zone['id']: zone for zone in tickets_zones}
        # for k,v in tickets_dict.items():
        #     id_withPrice = v['price_range']['id_withPrice']
        #     if id_withPrice in tickets_zones_dict:
        #         if tickets_zones_dict[id_withPrice]['pricetypes'] != '':
        #             tickets_dict[k]['price_range']['price'] = tickets_zones_dict[id_withPrice]['pricetypes'][0]['price']
        # return {
        #     "backend": "https://www.mydso.com",
        #     'event' : self.event,
        #     'venue': self.venue,
        #     'tickets': list(tickets_dict.values())}


def get_data(response, msg, ok=None):
    logger.info(f"{msg}: {response.status}")
    ok = ok or (200, 201)
    if response.status not in ok:
        logger.error(f"Request to {response.url} failed, existing")
        return
    return json.loads(response.body)
