import asyncio
import time
import os
import requests

URL = "http://api.meetup.com/2/open_events/?"


def fetch(items):
    results = {}
    session = requests.Session()
    for item in items:
        item.update(country="fr", key="43e6870567c1a23503117b756118c")
        time.sleep(.5)
        resp = session.get(URL + "&".join(["%s=%s" % i for i in item.items()]))
        data = resp.json()["results"]
        for result in data:
            results[int(result["id"])] = result
    return sorted(results.items(), reverse=True)


class Meetup(object):

    cities = ("paris", "lyon", "nantes")
    topics = ("python", "django")
    delay = 3600

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.log = bot.log
            self.loop = bot.loop
            plugin = bot.get_plugin("alain.alain3.AfpySocial").send_alain_tweet
            self.send_tweet = plugin.send_tweet
        else:
            self.loop = asyncio.get_event_loop()
            self.send_tweet = self._send_tweet
        self.loop.call_later(self.delay, self.check_tweets)
        self.last_meetup_id = os.path.expanduser("~/.irc3/last_meetup_id")

    def get_results(self):
        try:
            with open(self.last_meetup_id) as last_meetup_id:
                last_id = int(last_meetup_id.read())
        except (FileNotFoundError, ValueError):
            last_id = 0
        searches = []
        for city in self.cities:
            for topic in self.topics:
                searches.append(dict(topic=topic, city=city))
        results = fetch(searches)
        tweets = []
        for meetup_id, meetup in results:
            if meetup_id <= last_id:
                continue
            meetup["group_name"] = meetup["group"]["name"]
            tweets.append("[meetup] %(group_name)s - %(name)s - %(event_url)s" % meetup)
        with open(self.last_meetup_id, "w") as last_meetup_id:
            last_id = last_meetup_id.write(str(results[0][0]))
        return tweets

    def check_tweets(self):
        self.loop.call_later(self.delay, self.check_tweets)
        task = asyncio.gather(
            self.loop.run_in_executor(None, self.get_results),
            return_exceptions=True,
            loop=self.loop,
        )
        task.add_done_callback(self.send_tweets)
        return task

    def send_tweets(self, tweet_feed):
        for tweets in tweet_feed.result():
            if isinstance(tweets, list):
                for tweet in tweets:
                    self.send_tweet(tweet)
            else:
                self.bot.log.exception(tweets)

    def _send_tweet(self, tweet):
        self.bot.log.info(tweet)


def main():
    meetup = Meetup(None)
    meetup.loop.run_until_complete(meetup.check_tweets())


if __name__ == "__main__":
    main()
