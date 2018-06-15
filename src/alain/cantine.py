# -*- coding: utf-8 -*-
import urllib
import re


def check_page(url):
    page = urllib.urlopen(url)
    in_inscriptions = False
    registered = []
    for line in page.readlines():
        line = line.strip()
        if '<ul class="inscriptions"' in line:
            in_inscriptions = True
        elif "</ul>" in line:
            in_inscriptions = False
        elif in_inscriptions:
            match = re.search("<li>(.*)</li>", line)
            registered.append(match.groups()[0])
    return len(set(registered))


def check_events(filename):
    urls = []
    with open(filename) as fd:
        for line in fd:
            url = line.strip()
            if not url:
                continue
            amount = check_page(url)
            urls.append((amount, url))
    return urls
