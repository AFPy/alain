# -*- coding: utf-8 -*-
from irc3.plugins.command import command
from irc3.plugins.cron import cron
from irc3.plugins.social import Social
from irc3.plugins.social import TwitterAdapter
from datetime import datetime
from chut import sh
import feedparser
import requests
import logging
import random
import irc3


@irc3.plugin
class Alain(object):

    def __init__(self, bot):
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
            msg = 'Hey! Il y a des trucs à modérer: %s' % ' - '.join(entries)
            self.bot.privmsg(self.bot.config.channel, msg)

    @command(permission='admin')
    def restart(self, mask, target, args):
        """Restart a service

            %%restart (alain|members|docs|plone)
        """
        for name in ('alain', 'members', 'docs', 'plone'):
            if args.get(name):
                break
        try:
            if name in ('alain', 'members'):
                supervisor = sh['/usr/bin/sudo']
                for line in supervisor('/usr/bin/supervisorctl restart',
                                       name, combine_stderr=True):
                    yield line
            elif name == 'docs':
                pwd = sh.pwd()
                sh.cd('/home/afpy/AfpySphinx/docs')
                if not sh['hg']('pull -u'):
                    yield 'Failed to update code'
                else:
                    res = sh['make']('html').succeeded
                    sh.cd(pwd)
                    if res:
                        yield 'Docs build success'
                    else:
                        yield 'Docs build failure'
            elif name == 'plone':
                plone = sh['/home/afpy/afpy2012/plone/zinstance/bin/plonectl']
                for line in plone('restart', combine_stderr=True):
                    yield line
            else:
                yield 'moi pas connaitre %s' % name
        except OSError as e:
            yield repr(e)

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


@irc3.plugin
class Mon(object):

    requires = ['irc3.plugins.cron']
    defaults = dict(
        cron='*/3 * * * *',
        notify_after=2,
        verify='true',
        timeout=10)

    def __init__(self, bot):
        self.bot = bot
        self.config = dict(self.defaults,
                           **bot.config.get('irc3.plugins.mon', {}))
        self.log = logging.getLogger('irc3.plugins.mon')
        self.irc = logging.getLogger('irc.mon')
        self.irc.set_irc_targets(bot, self.bot.config['channel'])
        self.states = {}
        self.notify_after = int(self.config['notify_after'])
        self.verify = bool(self.config['verify'] == 'true')
        self.timeout = int(self.config['timeout'])
        self.bot.add_cron(self.config['cron'], self.check)

    def check_http(self, url):
        session = requests.Session()
        try:
            resp = session.get(url,
                               timeout=self.timeout,
                               verify=self.verify)
        except Exception as resp:
            return resp
        else:
            if resp.status_code != 200:
                return resp
    check_https = check_http

    def check(self):
        for name, url in self.config.items():
            if not isinstance(url, str):
                continue
            if '://' not in url:
                continue
            callback = getattr(self, 'check_' + url.split('://', 1)[0])
            state = self.states.setdefault(name, 0)
            self.log.debug('{0} state: {1}.'.format(name, state))
            resp = callback(url)
            if resp is None:
                if state >= self.notify_after:
                    self.irc.info('{0} fixed'.format(name))
                state = 0
            else:
                self.log.error('Error while checking {0}.'.format(name))
                if isinstance(resp, Exception):
                    self.log.exception(resp)
                else:
                    self.log.error(resp)
                state += 1
            if state == self.notify_after:
                self.irc.error('{0}({1}) {2}'.format(name, state, resp))
            elif state and state % (self.notify_after * 3) == 0:
                self.irc.error('{0}({1}) {2}'.format(name, state, resp))
            self.states[name] = state
