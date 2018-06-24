"""This is alain_afpy, our IRC bot on #afpy.

You can run it using `irc3 alain.ini`.
"""
import random
import re
from datetime import date

import feedparser
import requests
import irc3
from irc3.plugins.command import command
from irc3.plugins.cron import cron
from irc3.plugins.social import Social, TwitterAdapter


@irc3.plugin
class Alain(object):
    def __init__(self, bot):
        bot.config["channel"] = irc3.utils.as_channel(bot.config.channel)
        self.bot = bot
        self.session = requests.Session()

    @irc3.event(irc3.rfc.JOIN)
    def matin(self, mask=None, **_kwargs):
        if mask.nick.startswith(self.bot.nick):
            self.bot.privmsg(self.bot.config.channel, "matin")

    @irc3.event(r":(?P<mask>\S+) PRIVMSG {channel} :(lol|mdr)$")
    def lol(self, mask=None, channel=None, data=None):
        message = random.choice(("MDR", "hihihi", "HAHAHA", "mdr t'es con"))  # nosec
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(
        r":(?P<mask>\S+) PRIVMSG {channel} :"
        r".*\s(faudrai.|faut|ca serait bien que)\s+qu.*"
    )
    def yakafokon(self, mask=None, channel=None, data=None):
        message = "WARNING !!! YAKAFOKON DETECTED !!!!"
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(r":(?i)(?P<mask>\S+) PRIVMSG {channel} " r":.*\sapprendre.*python.*")
    def tutorial(self, mask=None, channel=None, data=None):
        message = (
            """Pour apprendre python vous pouvez commencer par ici: """
            "https://docs.python.org/fr/3/tutorial/index.html"
        )
        self.bot.privmsg(self.bot.config.channel, message)

    @irc3.event(r":(?P<mask>\S+) PRIVMSG {channel} :.*\soffre.*emploi.*")
    def job(self, mask=None, channel=None, data=None):
        self.bot.privmsg(
            self.bot.config.channel,
            "Pour poster une offre d'emploi veuillez consulter : "
            "https://www.afpy.org/post/edit/emplois",
        )

    @cron("10 9,11,14,17,20 * * *")
    def awaiting_review(self):
        status = self.session.get("https://www.afpy.org/status").json()
        todo = status["actualites"]["waiting"] + status["emplois"]["waiting"]
        if todo:
            msg = f"Hey! Il y a {todo} trucs à modérer !"
            self.bot.log.info("%r", msg)
            self.bot.privmsg(self.bot.config.channel, msg)

    def incoming_afpyros(self):
        feed = feedparser.parse(
            self.session.get("http://afpyro.afpy.org/afpyro.rss").text
        )
        now = date.today()
        for afpyro in feed.entries:
            afpyro_date = afpyro.updated_parsed.date()
            if afpyro_date >= now:
                yield afpyro_date, afpyro.link

    @cron("30 17 * * *")
    def afpyro_cron(self, force=False):
        messages = []
        now = date.today()
        for afpyro_date, link in self.incoming_afpyros():
            delta = afpyro_date - now
            message = ""
            if delta.days == 0:
                message = "Ca va commencer!!! %s" % link
            elif delta.days == 1:
                message = "C'est demain!!! %s" % link
            elif delta.days > 10 and (delta.days % 5 == 0 or force):
                message = "Prochain afpyro dans %s jours...... *loin* %s" % (
                    delta.days,
                    link,
                )
            elif delta.days > 5 and (delta.days % 3 == 0 or force):
                message = f"Prochain afpyro dans {delta.days} jours... {link}"
            elif delta.days > 0 and delta.days < 5:
                message = f"Prochain afpyro dans {delta.days} jours! {link}"
            if message:
                messages.append(message)
        if force:
            return messages
        for msg in messages:
            self.bot.privmsg(self.bot.config.channel, msg)
        return None

    @command(permission="view")
    def afpyro(self, *_args, **_kwargs):
        """Show incoming afpyro

            %%afpyro
        """
        for msg in self.afpyro_cron(force=True):
            yield msg


@irc3.plugin
class AfpySocial(Social):

    default_network = "twitter"
    networks = dict(
        alain=dict(
            adapter=TwitterAdapter,
            factory="twitter.Twitter",
            auth_factory="twitter.OAuth",
            domain="api.twitter.com",
            api_version="1.1",
            secure=True,
        ),
        pycon=dict(
            adapter=TwitterAdapter,
            factory="twitter.Twitter",
            auth_factory="twitter.OAuth",
            domain="api.twitter.com",
            api_version="1.1",
            secure=True,
        ),
    )

    @command(permission="edit")
    def tweet(self, mask, target, args):
        """Post to twitter

            %%tweet [pycon] <message>...
        """
        #    %%tweet (alain|pycon) <message>...
        if args["pycon"]:
            args["--id"] = "pycon"
        else:
            args["--id"] = "alain"
        super(AfpySocial, self).tweet(mask, target, args)

    def send_alain_tweet(self, message):
        for name, status in self.send_tweet(message, id="alain"):
            self.bot.log.info("[tweet] %s: %s", name, status)


# feeds

AFPY_DATES_PATTERNS = [
    re.compile(r"(\d{4})/(\d{2})/(\d{2}) (\d{,2}):(\d{2}):(\d{2})"),
    re.compile(r"(\d{4})-(\d{2})-(\d{2}) (\d{,2}):(\d{2}):(\d{2})"),
]


def parse_afpy_date(unparsed_date):
    """parse a UTC date in MM/DD/YYYY HH:MM:SS format"""
    for afpy_date_pattern in AFPY_DATES_PATTERNS:
        try:
            found = afpy_date_pattern.search(unparsed_date).groups()
            return tuple([int(i) for i in found] + [0, 0, 0])
        except AttributeError:
            pass


feedparser.registerDateHandler(parse_afpy_date)


def feed_dispatcher(bot):
    send_tweet = bot.get_plugin(AfpySocial).send_alain_tweet
    call_later = bot.loop.call_later

    def dispatcher(messages):
        for i, (_, message) in enumerate(messages):
            if "afpy" in message.lower():
                bot.log.info("Sending %r", message)
                # call_later(i + 1, bot.privmsg, c, m)
                call_later(i + 1, send_tweet, message)

    return dispatcher
