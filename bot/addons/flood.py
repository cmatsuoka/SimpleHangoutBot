# -*- coding: utf-8 -*-

'''
Flood control

This filter addon halts bot response if a flood is detected
'''

import time

from ..addon import Addon, ADDON


_NAME = 'flood'


class _FloodAddon(Addon):

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

        self._flood_count = { }
        self._flood_start = { }
        self._flood_time = 0

        if config.has_options('Flood', [ 'count', 'time', 'disable_time' ]):
            self._count = config.getint('Flood', 'count')
            self._time = config.getint('Flood', 'time')
            self._disable_time = config.getint('Flood', 'disable_time')
        else:
            config.add_option('Flood', 'count', '2')
            config.add_option('Flood', 'time', '2')
            config.add_option('Flood', 'disable_time', '5')


    def get_filters(self):
        return [ self._flood_control ]

    def _flood_control(self, conversation, user, text, reply_func):
        try:
            self._flood_count[conversation] += 1
        except:
            self._flood_count[conversation] = 1
            self._flood_start[conversation] = 0

        t = time.time()

        if self._flood_start[conversation]:
            if t - self._flood_start[conversation] > self._disable_time:
                # End of flood control
                self._flood_start[conversation] = 0
                return text
            else:
                # We're still flooded
                return None

        if t - self._flood_time > self._time:
            self._flood_time = t

            if self._flood_count[conversation] > self._count:
                self._flood_count[conversation] = 0
                self._flood_start[conversation] = t
                reply_func(conversation, 'Flood! 😬')
                return None

            self._flood_count[conversation] = 0

        return text


ADDON[_NAME] = _FloodAddon
