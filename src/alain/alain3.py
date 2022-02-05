"""This is alain_afpy, our IRC bot on #afpy.

You can run it using `irc3 alain.ini`.
"""
import random
import re
from datetime import date, datetime, timedelta

import feedparser
import requests
import irc3
from irc3.plugins.command import command
from irc3.plugins.cron import cron
from irc3.plugins.social import Social, TwitterAdapter


THANKS_WORDS = [
    " ".join((begin, mid, end)).strip()
    for begin in ["thx", "merci", "thanks", "Merci"]
    for mid in ["", "bro", "vieux"]
    for end in ["", "!", ":)", "♥", "!!", "☺"]
]


@irc3.plugin
class Alain:
    def __init__(self, bot):
        bot.config["channel"] = irc3.utils.as_channel(bot.config.channel)
        self.bot = bot
        self.last_awaiting_review = datetime(1970, 1, 1)
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
            "Pour poster une offre d'emploi, c'est par là : "
            "https://www.afpy.org/emplois/new",
        )

    @cron("*/5 9-21 * * *")
    def awaiting_review(self):
        status = self.session.get("https://www.afpy.org/status").json()
        admin_urls = {
            "actualites": "https://www.afpy.org/admin/news_moderation/",
            "emplois": "https://www.afpy.org/admin/jobs_moderation/",
        }
        todo = [
            admin_urls[post_type]
            for post_type in admin_urls
            if status[post_type]["waiting"]
        ]
        if todo and self.last_awaiting_review + timedelta(hours=2) < datetime.now():
            self.last_awaiting_review = datetime.now()
            msg = f"debnet, cyp, mdk, seluj78: {', '.join(todo)} !"
            self.bot.log.info("%r", msg)
            self.bot.privmsg(self.bot.config.channel, msg)

    @irc3.event(irc3.rfc.MY_PRIVMSG)
    def got_privmsg(self, mask=None, event=None, target=None, data=None, **kw):
        if any(
            done in data for done in {"done", "fait"}
        ) and self.last_awaiting_review > datetime.now() - timedelta(hours=2):
            self.last_awaiting_review = datetime(1970, 1, 1)
            self.bot.privmsg(
                self.bot.config.channel, random.choice(THANKS_WORDS)  # nosec
            )


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
        """Post to twitter.

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


def feed_dispatcher(bot):
    send_tweet = bot.get_plugin(AfpySocial).send_alain_tweet
    call_later = bot.loop.call_later

    def dispatcher(messages):
        messages = list(messages)
        bot.log.info("Dispatching %d feed items", len(messages))
        bot.call_many("privmsg", messages)
        for i, (_, message) in enumerate(messages):
            if "afpy" in message.lower():
                bot.log.info("Sending %r", message)
                # call_later(i + 1, bot.privmsg, c, m)
                call_later(i + 1, send_tweet, message)

    return dispatcher
