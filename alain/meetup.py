# -*- coding: utf-8 -*-
try:
    from irc3.compat import asyncio
except ImportError:
    import asyncio
import requests
import time
import os

url = 'http://api.meetup.com/2/open_events/?'


def fetch(items):
    results = {}
    session = requests.Session()
    for item in items:
        item.update(
            country='fr',
            key='43e6870567c1a23503117b756118c',
        )
        time.sleep(.5)
        resp = session.get(url + '&'.join(['%s=%s' % i for i in item.items()]))
        data = resp.json()['results']
        for r in data:
            results[int(r['id'])] = r
    return sorted(results.items(), reverse=True)


class Meetup(object):

    cities = ('paris', 'lyon', 'nantes',)
    topics = ('python', 'django',)
    delay = 3600

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.log = bot.log
            self.loop = bot.loop
            plugin = bot.get_plugin('alain.alain3.AfpySocial').send_alain_tweet
            self.send_tweet = plugin.send_tweet
        else:
            self.loop = asyncio.get_event_loop()
        self.loop.call_later(self.delay, self.check_tweets)
        self.fd = os.path.expanduser('~/.irc3/last_meetup_id')

    def get_results(self):
        try:
            with open(self.fd) as fd:
                last_id = int(fd.read())
        except:
            last_id = 0
        searches = []
        for city in self.cities:
            for topic in self.topics:
                searches.append(dict(topic=topic, city=city))
        results = fetch(searches)
        tweets = []
        for id, r in results:
            if id <= last_id:
                continue
            r['group_name'] = r['group']['name']
            tweets.append(
                '[meetup] %(group_name)s - %(name)s - %(event_url)s' % r)
        with open(self.fd, 'w') as fd:
            last_id = fd.write(str(results[0][0]))
        return tweets

    def check_tweets(self):
        self.loop.call_later(self.delay, self.check_tweets)
        task = asyncio.gather(
            self.loop.run_in_executor(None, self.get_results),
            return_exceptions=True,
            loop=self.loop)
        task.add_done_callback(self.send_tweets)
        return task

    def send_tweets(self, f):
        for tweets in f.result():
            if isinstance(tweets, list):
                for tweet in tweets:
                    self.send_tweet(tweet)
            else:
                self.bot.log.exception(tweets)

    def send_tweet(self, tweet):
        self.bot.log.info(tweet)

if __name__ == '__main__':
    m = Meetup(None)
    m.loop.run_until_complete(m.check_tweets())
