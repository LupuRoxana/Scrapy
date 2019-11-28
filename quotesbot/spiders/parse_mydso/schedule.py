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
            for schedule_result in self.extract_schedule_page(response):
                yield schedule_result

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
                buy_url = f"https://www.mydso.com{event['uri']}"
                event_name = event['title'].replace("\xa0", " & ")
                ev = EventParser(event_name, ep['id'], buy_url, ep['date'])

                url = f"https://www.mydso.com/h/syos/SyosSummary?houseid=meyerson&id={ep['id']}&type=perf"
                # print(url)
                yield JSONRequest(url, method="GET", callback=ev.parse_performance_seats)


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

    def parse_performance_seats(self, response):
        data = json.loads(response.body)
        tickets_sections = data['sections']
        print('!!!!!!!!!!!!!!!!!')
        tickets_zones = data['zones']
        # print(tickets_zones)
        tickets_dict = {}
        for ticket in tickets_sections:
            ticket_id = str(ticket['id'])
            if ticket['id'] not in tickets_dict:
                tickets_dict[ticket_id] = {"name":ticket['name'], "total":ticket['total'], "available":ticket['avail']}
        # pprint(tickets_dict)
        for price_zone in tickets_zones:
                        for
            print(section_id)
            if section_id in tickets_dict:
                tickets_dict[section_id].__setitem__('price', price_zone['price'])
                # print(tickets_dict[section_id])
                # tickets_dict[[price_zones['sections']['id']]['price'] = price_zones['price']





    def get_data(self, response, msg, ok=None):
        self.logger.info(f"{msg}: {response.status}")

        ok = ok or (200, 201)
        if response.status not in ok:
            self.logger.error(f"Request to {response.url} failed, existing")
            return

        return json.loads(response.body)
