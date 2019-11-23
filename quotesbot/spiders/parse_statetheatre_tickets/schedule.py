
import json
from pprint import pprint



class Event(object):
    def __init__(self, EventID, Event, PerformanceName, Description, PerformanceDateTime, TimeZone, SeatMapUrl, DisplayIcon):
        self.EventID = EventID
        self.Event = Event
        self.PerformanceName = PerformanceName
        self.Description = Description
        self.PerformanceDateTime = PerformanceDateTime
        self.TimeZone = TimeZone
        self.SeatMapUrl = SeatMapUrl
        self.DisplayIcon = DisplayIcon

    def prtFunction(self):
        print(
            f"{self.EventID} {self.Event} {self.PerformanceName} {self.Description} {self.PerformanceDateTime} {self.TimeZone} {self.SeatMapUrl} {self.DisplayIcon}")





def extract_schedule_page(self, response):

    print('Parsing events page !!!!!!!!!!!!!!!!!\n\n\n\n\n')
    # pprint(json.loads(response.body))
    event_list = self.get_data(response, "Received events")
    event_list = event_list["performance"]
    pprint(event_list)
    count = 0
    new_path = 'C:/Users/RoxanaLupu/Documents/quotesbot/events.txt'
    new_days = open(new_path, 'w')

    for event in event_list:
        seatMapUrl = f"https://statetheatre.showare.com/orderticketsvenue.asp?p={event['PerformanceID']}"
        e1 = Event(event['EventID'], event['Event'], event['PerformanceName'], event['Description'], event['PerformanceDateTime'],
                   event['TimeZone'], seatMapUrl, event['DisplayIcon'])
        e1.prtFunction();
    print("========================================")



def get_data(self, response, msg, ok=None):
    self.logger.info(f"{msg}: {response.status}")

    ok = ok or (200, 201)
    if response.status not in ok:
        self.logger.error(f"Request to {response.url} failed, existing")
        return

    return json.loads(response.body)
