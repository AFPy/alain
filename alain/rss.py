# -*- coding: utf-8 -*-
import feedparser

def awaiting():
    feed = feedparser.parse(
      'http://www.afpy.org/search_rss?sort_on=Date&sort_order=reverse&review_state=pending')
    entries = [str(e.id).replace('zope.afpy.org', 'www.afpy.org') for e in feed.entries]
    if entries:
        return 'Hey! Il y a des trucs à modérer: %s' % ' - '.join(entries)
    return ''

if __name__ == '__main__':
    print awaiting()
