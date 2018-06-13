# -*- coding: utf-8 -*-
from datetime import datetime
import feedparser


def incoming_afpyros():
    feed = feedparser.parse(
        'http://afpyro.afpy.org/afpyro.rss')
    now = datetime.now()
    now = datetime(now.year, now.month, now.day)
    incomings = []
    for e in feed.entries:
        t = e.updated_parsed
        d = datetime(t.tm_year, t.tm_mon, t.tm_mday)
        if d >= now:
            incomings.append((d, e.link))
    return incomings

if __name__ == '__main__':
    print incoming_afpyros()
