# -*- coding: utf-8 -*-
import datetime
import httplib
import functools
import os

def dayly(h, m):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            self.logger.info('Entering cron %s', func.__name__)
            now = datetime.datetime.now()
            cron = os.path.join(self.config.bot.var,
                                func.__name__+'.cron')
            current = now.strftime('%d-%m-%Y')
            latest = None
            if os.path.isfile(cron):
                with open(cron) as fd:
                    latest = fd.read()
            self.logger.info('%s %s', current, latest)
            if current == latest:
                return ''
            result = ''
            if now.hour >= h and now.minute >= m:
                result = func(self, *args, **kwargs)
                with open(cron, 'w') as fd:
                    fd.write(now.strftime('%d-%m-%Y'))
            self.logger.info('Cron return %s', result)
            return result
        return wrapped
    return wrapper


