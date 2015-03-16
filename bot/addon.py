# -*- coding: utf-8 -*-

import hangups
import asyncio
import bot.util

from bot.util import *

class Addon(object):
    author = ''
    version = ''
    requires = [ ]

    def __init__(self, config, name):
        if name != None:
            self.name = name
        self._data = ()
        self._config = config
        self.bot_name = config.get('Global', 'name')
        self.dbfile = config.get('Global', 'dbfile')

    def get_parsers(self):
        return [ ]

    def get_filters(self):
        return [ ]

    def get_timers(self):
        return [ ]

    def set_client(self, client):
        self._client = client

    # Low-level hooks

    def on_connect(self, initial_data, user_list, conv_list):
        self._user_list = user_list
        self._conv_list = conv_list

    def on_event(self, conv_event):
        pass

    def on_disconnect(self):
        self._user_list = None
        self._conv_list = None

    # helpers

    def report(self, text):
        report('\033[1;34m[{}]\033[0m {}'.format(self.name, text))

    def _send_user_message(self, user_id, message):
        for conv in self._conv_list.get_all():
            participants = sorted((user for user in conv.users if not user.is_self), key=lambda user: user_id)
            if (len(participants) == 1 and participants[0].id_.chat_id == user_id):
               segments = [ hangups.ChatMessageSegment(message) ]
               asyncio.async(conv.send_message(segments))


ADDON = { }

def all():
    return ADDON.keys()

def addons(config):
    retval = [ ]
    loaded = [ ]

    for i in config.getlist('Global', 'addons'):
        try:
            addon = ADDON[i]
        except:
            report('** Skip addon **: {} not defined'.format(i))
            continue

        reqs = ','.join(addon.requires) 

        if len(reqs) > 0 and not set(addon.requires).issubset(set(loaded)):
            report('** Skip addon **: {} (requires {})'.format(i, reqs))
        elif i in loaded:
            report('** Skip addon **: {} (already loaded)'.format(i))
        else:
            name = i
            if addon.version:
                name += ' ' + addon.version
            if addon.author:
                name += ' by ' + addon.author
            if len(reqs) > 0:
                name += ' [{}]'.format(reqs)
            report('Initialize addon: ' + name)

            retval.append(addon(config))
            loaded.append(i)

    if config.changed():
        config.write()

    return retval

