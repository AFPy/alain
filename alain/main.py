# -*- coding: utf-8 -*-
from irc import IRCBot, IRCConnection as BaseConn
from ConfigObject import ConfigObject
from irc import socket
from functools import wraps
import random
import httplib
import time
import stat
import sys
import os


class HTTPPing(object):

    def __init__(self, host, port, path, timeout=30):
        self.host, self.port, self.path, self.timeout = host, port, path, timeout
        self.status = True
        self.reason = ''

    def ping(self):
        if self.port == 443:
            conn = httplib.HTTPSConnection(self.host, self.port)
        else:
            conn = httplib.HTTPConnection(self.host, self.port)
        try:
            conn.request('GET', self.path)
            resp = conn.getresponse()
        except Exception, e:
            self.status = False
            self.reason = str(e)
        else:
            if resp.status == 200:
                self.status = True
                self.reason = ''
            else:
                self.status = False
                self.reason = '%s %s' % (resp.status, resp.reason)

class IRCConnection(BaseConn):

    def connect(self):
        """\
        Connect to the IRC server using the nickname
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._sock.connect((self.server, self.port))
        except socket.error:
            self.logger.error('Unable to connect to %s on port %d' % (self.server, self.port), exc_info=1)
            sys.exit(1)

        self._sock_file = self._sock.makefile()

        self.send("USER alain %s bla :I'm Alain. The AFPy mascot" % (self.server,))
        self.logger.info('Authing as %s' % self.nick)

        # send NICK command as soon as authing
        self.register_nick()

    def handle_ping(self, payload):
        """\
        Respond to periodic PING messages from server
        """
        self.logger.info('server ping: %s' % payload)
        self.send('PONG %s' % payload)
        self.mon()

    def ghost(self):
        if self.config.bot.password:
            nick = self.config.bot.nick
            self.send('PRIVMSG nickserv :ghost %s %s ' % (nick, self.config.bot.password))
            time.sleep(2)
            self.nick = nick
            self.send('NICK %s' % self.nick)
            time.sleep(2)
            self.send('PRIVMSG nickserv :identify %s' % self.config.bot.password)

    def mon(self, verbose=False):
        for name, s in self.services:
            status = s.status
            s.ping()

            if status and s.status:
                message = '- %s: UP' % name
            elif status and not s.status:
                message = '- %s: FAILURE %s' % (name, s.reason)
            elif not status and s.status:
                message = '- %s: FIXED' % name

            if verbose:
                self.respond(message, self.channel)
            elif not status or not s.status:
                self.respond(message, self.channel)
            self.logger.info(message)

def sudoers_command(func):
    @wraps(func)
    def wrapper(self, nick, message, channel):
        if nick not in sudoers or not channel:
            return 'matin %s' % nick
        return func(self, nick, message, channel)
    return wrapper


class Alain(IRCBot):

    @sudoers_command
    def identify(self, nick, message, channel):
        """Recuperation de pseudo"""
        self.conn.ghost()
        return '%s: Thanks!' % nick

    @sudoers_command
    def status(self, nick, message, channel):
        """Status des services HTTP"""
        self.conn.respond('Checking services...', channel)
        self.conn.mon(verbose=True)
        return 'Done.'

    @sudoers_command
    def clean(self, nick, message, channel):
        """Supprime les doublons dans ce que je dis"""
        messages = []
        with open(self.config.bot.db) as fd:
            messages = set([l for l in fd.readlines() if l.strip()])
        with open(self.config.bot.db, 'w') as fd:
            for message in messages:
                fd.write(message)
        return "Ca c'est fait"

    def matin(self, nick, message, channel):
        """Ping"""
        return '%s: matin' % nick

    def help(self, nick, message, channel):
        """Affiche l'aide"""
        self.respond('Available commands are:', channel)
        for k, v in self.__class__.__dict__.items():
            if not k.startswith('_') and getattr(v, '__doc__', None):
                self.respond('- %s: %s' % (k, v.__doc__.strip()), channel)
        return ''

    def offre_emploi(self, *args, **kwargs):
        return ('''Pour poster une offre d'emploi veuillez consulter:'''
                ' http://www.afpy.org/docs/faq.html#comment-puis-je-poster-une-offre-d-emloi')

    def faq(self, *args, **kwargs):
        """URL de la FAQ"""
        return 'http://www.afpy.org/docs/faq.html'

    def admins(self, *args, **kwargs):
        """Liste des gens sudoers sur py.afpy.org"""
        return ', '.join(self.sudoers)


    def add_message(self, message):
        with open(self.config.bot.db, 'a+') as fd:
            fd.write(message+'\n')

    def get_message(self):
        pos = random.randint(0, os.stat('var/messages.txt')[stat.ST_SIZE])
        with open(self.config.bot.db) as fd:
            fd.seek(pos)
            fd.readline()
            try:
                return fd.readline()
            except:
                return 'matin'

    def ia(self, nick, message, channel):
        if not channel:
            return ''
        for k in self.__class__.__dict__:
            if message.startswith(k):
                return ''
        self.add_message(message)
        return '%s: %s' % (nick, self.get_message())

    def command_patterns(self):
        commands = []
        for k, v in self.__class__.__dict__.items():
            if not k.startswith('_') and getattr(v, '__doc__', None):
                commands.append(self.ping('^%s$' % k, getattr(self, k)))
        return commands + [
            ('(.*\soffre.*emploi.*)', self.offre_emploi),
            self.ping('(.*)', self.ia),
        ]


sudoers = (
    'ccomb',
    'gawel',
    'ogrisel',
    'jpcw',
    'tarek',
    'NelleV',
  )
services = (
        ('www', HTTPPing('www.afpy.org', 80, '/')),
        ('varnish', HTTPPing('www.afpy.org', 8000, '/')),
        ('membres', HTTPPing('www.afpy.org', 80, '/membres/login')),
        ('hg', HTTPPing('hg.afpy.org', 443, '/')),
        ('afpyro', HTTPPing('afpy.ro', 80, '/faq.html')),
        ('pycon', HTTPPing('www.pycon.fr', 80, '/conference/edition2011')),
        ('logs', HTTPPing('logs.afpy.org', 80, '/')),
        ('fld', HTTPPing('front-de-liberation-des-developpeurs.org', 80, '/')),
    )


def main():
    config = ConfigObject(defaults=dict(here=os.getcwd()))
    config.read(os.path.expanduser('~/.alainrc'))
    conn = IRCConnection('irc.freenode.net', 6667, config.bot.nick+'_',
                         verbosity=config.bot.verbosity.as_int(),
                         logfile=config.bot.logfile or None)
    conn.config = config
    conn.channel = config.bot.channel
    conn.services = services
    conn.connect()
    time.sleep(3)
    conn.ghost()
    bot = Alain(conn)
    bot.config = config
    bot.channel = config.bot.channel
    bot.sudoers = sudoers
    bot.messages = []
    conn.join(config.bot.channel)
    time.sleep(2)
    conn.respond('matin', config.bot.channel)
    conn.mon()
    conn.enter_event_loop()


