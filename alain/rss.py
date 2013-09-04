# -*- coding: utf-8 -*-
from ConfigObject import ConfigObject
import feedparser
import os

config = ConfigObject(defaults=dict(here=os.getcwd()))
config.read(os.path.expanduser('~/.alainrc'))
cred = config.plone.user


def awaiting():
    feed = feedparser.parse(
        'http://%s@www.afpy.org/search_rss?review_state=pending' % cred)
    entries = [str(e.id) for e in feed.entries]
    entries = [e for e in entries if '/forums/' not in e]
    if entries:
        return 'Hey! Il y a des trucs à modérer: %s' % ' - '.join(entries)
    return ''

if __name__ == '__main__':
    print awaiting()
