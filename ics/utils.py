#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

import arrow
from arrow.arrow import Arrow
tzutc = arrow.utcnow().tzinfo
from uuid import uuid4

import re

from . import parse
from datetime import timedelta


def remove_x(container):
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name.startswith('X-'):
            del container[i]


def iso_to_arrow(time_container, available_tz={}):
    if time_container is None:
        return None

    # TODO : raise if not iso date
    tz_list = time_container.params.get('TZID')
    # TODO : raise if len(tz_list) > 1 or if tz is not a valid tz
    # TODO : see if timezone is registered as a VTIMEZONE
    if tz_list and len(tz_list) > 0:
        tz = tz_list[0]
    else:
        tz = None
    if (not 'T' in time_container.value) and \
            'DATE' in time_container.params.get('VALUE', []):
        val = time_container.value + 'T0000'
    else:
        val = time_container.value

    if tz and not (val[-1].upper() == 'Z'):
        naive = arrow.get(val).naive
        selected_tz = available_tz.get(tz, 'UTC')
        return arrow.get(naive, selected_tz)
    else:
        return arrow.get(val)

    # TODO : support floating (ie not bound to any time zone) times (cf
    # http://www.kanzaki.com/docs/ical/dateTime.html)


def iso_precision(string):
    has_time = 'T' in string

    if has_time:
        date_string, time_string = string.split('T', 1)
        time_parts = re.split('[+-]', time_string, 1)
        has_seconds = time_parts[0].count(':') > 1
        has_seconds = not has_seconds and len(time_parts[0]) == 6

        if has_seconds:
            return 'second'
        else:
            return 'minute'
    else:
        return 'day'


def get_lines(container, name):
    lines = []
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name == name:
            lines.append(item)
            del container[i]
    return lines

def parse_recurrent(line):

    WEEKDAYS = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]

    def freq(frequency):

        FREQ = {"SECONDLY" : timedelta(seconds = 1),
            "MINUTELY" : timedelta(minutes = 1),
            "HOURLY" : timedelta(hours = 1),
            "DAILY" : timedelta(days = 1),
            "WEEKLY" : timedelta(weeks = 1),
            "MONTHLY" : timedelta(weeks = 52),
            "YEARLY" : timedelta(weeks = 52 * 12)
        }

        return FREQ[frequency] if frequency in FREQ else None
        
    def until(enddate):
        
        return enddate
        
    def count(digit):
    
        if len(digit) > 1:
            raise Exception("Digit must be one digit")
            
        return digit
        
    def interval(digit):
    
        if len(digit) > 1 or digit < 0:
            raise Exception("Digit must be one positive digit")
        
        return digit
        
    def bysecond(byseclist):
    
        byseclist = byseclist.split(",")
        
        for seconds in byseclist:
            if not 0 <= seconds <= 60:
                raise Exception("Seconds must be between 0 and 60")
    
        return byseclist
    
    def byminute(byminlist):

        byminlist = byminlist.split(",")
        
        for minutes in byminlist:
            if not 0 <= minutes <= 59:
                raise Exception("Minutes must be between 0 and 59")
    
        return byminlist
    
    def byhour(byhrlist):
        
        byhrlist = byhrlist.split(",")
        
        for hour in byhrlist:
            if not 0 <= hour <= 23:
                raise Exception("Hours must be between 0 and 23")
    
        return byhrlist
        
    def byday(bywdaylist):
    
        bywdaylist = bywdaylist.split(",")
    
        for weekdaynum in bywdaylist:
        
            sign, ordwk, weekday = re.search('([+,-])?(\d*)(\w*)', weekdaynum).groups()
        
            if ordwk and not 1 <= ordwk <= 53:
                raise Exception("Week of year must be between 1 and 53")
                
            if weekday not in WEEKDAYS:
                raise Exception("Unknown weekday")
        
        return bywdaylist if len(bywdaylist) > 1 else bywdaylist[0]
    
    def bymonthday(bymodaylist):
        
        bymodaylist = bymodaylist.split(",")
        
        for monthdaynum in bymodaylist:
        
            sign, ordmoday = re.search('([+,-])?(\w*)', monthdaynum).groups()
        
            if not 1 <= ordmoday <= 31:
                raise Exception("Day of month must be between 1 and 31")
    
        return bymodaylist
    
    def byyearday(byyrdaylist):
        
        byyrdaylist = byyrdaylist.split(",")
        
        for yeardaynum in byyrdaylist:
        
            sign, ordyrday = re.search('([+,-])?(\w*)', yeardaynum).groups()
        
            if not 1 <= ordyrday <= 366:
                raise Exception("Day of year must be between 1 and 366")
    
        return byyrdaylist
        
    def byweekno(bywknolist):
        
        bywknolist = bywknolist.split(",")
        
        for weeknum in bywknolist:
        
            sign, ordwk = re.search('([+,-])?(\w*)', weeknum).groups()
        
            if not 1 <= ordwk <= 53:
                raise Exception("Week must be between 1 and 53")
    
        return bywknolist
        
    def bymonth(bymolist):
        
        bymolist = bymolist.split(",")
        
        for monthnum in bymolist:
        
            if not 1 <= monthnum <= 12:
                raise Exception("Month must be between 1 and 12")
    
        return bymolist
        
    def bysetpos(bysplist):
        
        return byyearday(bysplist)
        
    def wkst(weekday):
    
        if weekday not in WEEKDAYS:
            raise Exception("Unknown weekday")
                
        return weekday

    rules = {"FREQ" : freq, "UNTIL" : until, "COUNT" : count, "INTERVAL" : interval, "BYSECOND" : bysecond, "BYMINUTE" : byminute,
        "BYHOUR" : byhour, "BYDAY" : byday, "BYMONTHDAY" : bymonthday, "BYYEARDAY" : byyearday, "BYWEEKNO" : byweekno, "BYMONTH" : bymonth, 
        "BYSETPOS" : bysetpos, "WKST" : wkst}
    
    to_return = {}
    
    # line = "RRULE:FREQ=MONTHLY;INTERVAL=2;BYDAY=TU"
    # [['FREQ', 'MONTHLY'], ['INTERVAL', '2'], ['BYDAY', 'TU']]
    parts = map(lambda x : x.split("="), line.split(":")[1].split(";"))
    for part in parts:
        if part[0] not in rules:
            continue
        name = part[0]
        to_return[name.lower()] = rules[name](part[1])
    print(to_return) # debug
    
    if not 'freq' in to_return:
        raise Exception("Recurrent must contain 'FREQ'")
    
    if 'until' and 'count' in to_return:
        raise Exception("Recurrent cannot contain 'UNTIL' and 'COUNT'")
        
    return to_return


def parse_duration(line):
    """
    Return a timedelta object from a string in the DURATION property format
    """
    DAYS, SECS = {'D': 1, 'W': 7}, {'S': 1, 'M': 60, 'H': 3600}
    sign, i = 1, 0
    if line[i] in '-+':
        if line[i] == '-':
            sign = -1
        i += 1
    if line[i] != 'P':
        raise parse.ParseError()
    i += 1
    days, secs = 0, 0
    while i < len(line):
        if line[i] == 'T':
            i += 1
            if i == len(line):
                break
        j = i
        while line[j].isdigit():
            j += 1
        if i == j:
            raise parse.ParseError()
        val = int(line[i:j])
        if line[j] in DAYS:
            days += val * DAYS[line[j]]
            DAYS.pop(line[j])
        elif line[j] in SECS:
            secs += val * SECS[line[j]]
            SECS.pop(line[j])
        else:
            raise parse.ParseError()
        i = j + 1
    return timedelta(sign * days, sign * secs)


def timedelta_to_duration(dt):
    """
    Return a string according to the DURATION property format
    from a timedelta object
    """
    days, secs = dt.days, dt.seconds
    res = 'P'
    if days // 7:
        res += str(days // 7) + 'W'
        days %= 7
    if days:
        res += str(days) + 'D'
    if secs:
        res += 'T'
        if secs // 3600:
            res += str(secs // 3600) + 'H'
            secs %= 3600
        if secs // 60:
            res += str(secs // 60) + 'M'
            secs %= 60
        if secs:
            res += str(secs) + 'S'
    return res


def get_arrow(value):
    if value is None:
        return None
    elif isinstance(value, Arrow):
        return value
    elif isinstance(value, tuple):
        return arrow.get(*value)
    elif isinstance(value, dict):
        return arrow.get(**value)
    else:
        return arrow.get(value)


def arrow_to_iso(instant):
    # set to utc, make iso, remove timezone
    instant = arrow.get(instant.astimezone(tzutc)).format('YYYYMMDDTHHmmss')
    return instant + 'Z'


def uid_gen():
    uid = str(uuid4())
    return "{}@{}.org".format(uid, uid[:4])
