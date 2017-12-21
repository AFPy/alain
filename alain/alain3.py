# -*- coding: utf-8 -*-
from irc3.plugins.command import command
from irc3.plugins.cron import cron
from irc3.plugins.social import Social
from irc3.plugins.social import TwitterAdapter
from irc3.compat import asyncio
from datetime import datetime
from functools import partial
from chut import sh
import feedparser
import requests
import logging
import random
import irc3
import re


@irc3.plugin
class Alain(object):

    def __init__(self, bot):
        bot.config['channel'] = irc3.utils.as_channel(bot.config.channel)
        self.bot = bot
        self.session = requests.Session()
        self.plone = requests.Session()
        try:
            self.plone.auth = tuple(self.bot.config.alain['plone'].split(':'))
        except:
            pass

    @irc3.event(irc3.rfc.JOIN)
    def matin(self, mask=None, **kw):
        if mask.nick.startswith(self.bot.nick):
            self.bot.privmsg(self.bot.config.channel, 'matin')

    @irc3.event(':(?P<mask>\S+) PRIVMSG {channel} :(lol|mdr)$')
    def lol(self, mask=None, channel=None, data=None):
        message = random.choice(('MDR', 'hihihi', 'HAHAHA', "mdr t'es con"))
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(':(?P<mask>\S+) PRIVMSG {channel} :'
                '.*\s(faudrai.|faut|ca serait bien que)\s+qu.*')
    def yakafokon(self, mask=None, channel=None, data=None):
        message = 'WARNING !!! YAKAFOKON DETECTED !!!!'
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(
        ':(?i)(?P<mask>\S+) PRIVMSG {channel} :.*\sapprendre.*python.*')
    def tutorial(self, mask=None, channel=None, data=None):
        message = (
            '''Pour apprendre python vous pouvez commencer par ici: '''
            'https://docs.python.org/fr/3/tutorial/index.html'
        )
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(':(?P<mask>\S+) PRIVMSG {channel} :.*\soffre.*emploi.*')
    def job(self, mask=None, channel=None, data=None):
        message = (
            '''Pour poster une offre d'emploi veuillez consulter:'''
            ' http://www.afpy.org/doc/afpy/faq.html'
            '#comment-puis-je-poster-une-offre-d-emploi')
        self.bot.privmsg(self.bot.config.channel, message)

    @cron('10 9,11,14,17,20 * * *')
    def awaiting_review(self):
        url = 'http://www.afpy.org/search_rss?review_state=pending'
        feed = feedparser.parse(self.plone.get(url).text)
        entries = [str(e.id) for e in feed.entries]
        entries = [e for e in entries if '/forums/' not in e]
        if entries:
            msg = u'Hey! Il y a des trucs à modérer: %s' % ' - '.join(entries)
            self.bot.log.info('%r', msg)
            self.bot.privmsg(self.bot.config.channel, msg)

    def incoming_afpyros(self):
        feed = feedparser.parse(self.session.get(
            'http://afpyro.afpy.org/afpyro.rss').text)
        now = datetime.now()
        now = datetime(now.year, now.month, now.day)
        for e in feed.entries:
            t = e.updated_parsed
            d = datetime(t.tm_year, t.tm_mon, t.tm_mday)
            if d >= now:
                yield d, e.link

    @cron('30 17 * * *')
    def afpyro_cron(self, force=False):
        messages = []
        now = datetime.now()
        now = datetime(now.year, now.month, now.day)
        for date, link in self.incoming_afpyros():
            delta = date - now
            message = ''
            if delta.days == 0:
                message = 'Ca va commencer!!! %s' % link
            elif delta.days == 1:
                message = 'C\'est demain!!! %s' % link
            elif delta.days > 10 and (delta.days % 5 == 0 or force):
                message = 'Prochain afpyro dans %s jours...... *loin* %s' % (
                    delta.days, link)
            elif delta.days > 5 and (delta.days % 3 == 0 or force):
                message = 'Prochain afpyro dans %s jours... %s' % (
                    delta.days, link)
            elif delta.days > 0 and delta.days < 5:
                message = 'Prochain afpyro dans %s jours! %s' % (
                    delta.days, link)
            if message:
                messages.append(message)
        if force:
            return messages
        for msg in messages:
            self.bot.privmsg(self.bot.config.channel, msg)

    @command(permission='view')
    def afpyro(self, *args, **kwargs):
        """Show incoming afpyro

            %%afpyro
        """
        for msg in self.afpyro_cron(force=True):
            yield msg


@irc3.plugin
class AfpySocial(Social):

    default_network = 'twitter'
    networks = dict(
        alain=dict(
            adapter=TwitterAdapter,
            factory='twitter.Twitter',
            auth_factory='twitter.OAuth',
            domain='api.twitter.com',
            api_version='1.1',
            secure=True
        ),
        pycon=dict(
            adapter=TwitterAdapter,
            factory='twitter.Twitter',
            auth_factory='twitter.OAuth',
            domain='api.twitter.com',
            api_version='1.1',
            secure=True
        ),
    )

    @command(permission='edit')
    def tweet(self, mask, target, args):
        """Post to twitter

            %%tweet [pycon] <message>...
        """
        #    %%tweet (alain|pycon) <message>...
        if args['pycon']:
            args['--id'] = 'pycon'
        else:
            args['--id'] = 'alain'
        super(AfpySocial, self).tweet(mask, target, args)

    def send_alain_tweet(self, message):
        for name, status in self.send_tweet(message, id='alain'):
            self.bot.log.info('[tweet] %s: %s', name, status)


# feeds

_afpy_dates = [
    re.compile(r'(\d{4})/(\d{2})/(\d{2}) (\d{,2}):(\d{2}):(\d{2})'),
    re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{,2}):(\d{2}):(\d{2})'),
]


def afpy_date(dt):
    """parse a UTC date in MM/DD/YYYY HH:MM:SS format"""
    g = None
    for afpy_date in _afpy_dates:
        try:
            g = afpy_date.search(dt).groups()
        except:
            pass
    if g:
        return tuple([int(i) for i in g] + [0, 0, 0])
feedparser.registerDateHandler(afpy_date)


def feed_dispatcher(bot):
    send_tweet = bot.get_plugin(AfpySocial).send_alain_tweet
    call_later = bot.loop.call_later

    def dispatcher(messages):
        for i, (c, m) in enumerate(messages):
            if u'afpy' in m.lower():
                bot.log.info('Sending %r', m)
                # call_later(i + 1, bot.privmsg, c, m)
                call_later(i + 1, send_tweet, m)
    return dispatcher
