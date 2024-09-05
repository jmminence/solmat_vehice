import urllib.request
import json

from datetime import datetime

from dateutil.parser import ParserError, parse
from django.db.models import Func, IntegerField


class YearWeek(Func):
    function = "YEARWEEK"
    template = "%(function)s(%(expressions)s)"
    output_field = IntegerField()


def get_holidays():
    currentDate = datetime.now().date()
    URL = f"https://apis.digital.gob.cl/fl/feriados/{currentDate.year}"
    headers = {"User-Agent": "Vehice/1.0"}

    request = urllib.request.Request(URL, headers=headers)

    holidays = []

    with urllib.request.urlopen(request) as response:
        response_json = json.load(response)

        for holiday in response_json:
            try:
                date = parse(holiday["fecha"])
            except ParserError:
                continue
            else:
                holidays.append(date)

    return holidays
