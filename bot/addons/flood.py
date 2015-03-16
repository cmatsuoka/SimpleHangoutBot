# -*- coding: utf-8 -*-

'''
Flood control

This filter addon halts bot response if a flood is detected
'''

import time

from ..addon import Addon, ADDON

_NAME = 'flood'


class _FloodAddon(Addon):
    version = '0.1'

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

        self._flood_count = { }
        self._flood_start = { }
        self._flood_time = 0

        s = _NAME.capitalize()

        if config.has_options(s, [ 'count', 'time', 'disable_time' ]):
            self._count = config.getint(s, 'count')
            self._time = config.getint(s, 'time')
            self._disable_time = config.getint(s, 'disable_time')
        else:
            config.add_option(s, 'count', '2')
            config.add_option(s, 'time', '2')
            config.add_option(s, 'disable_time', '5')


    def get_filters(self):
        return [ self._flood_control ]

    def _flood_control(self, conversation, user, text, reply_func):
        try:
            self._flood_count[conversation]
        except:
            self._flood_count[conversation] = 0
            self._flood_start[conversation] = 0

        if user.is_self:
            self._flood_count[conversation] += 1

        t = time.time()

        if self._flood_start[conversation]:
            if t - self._flood_start[conversation] > self._disable_time:
                # End of flood control
                self.report('Not flooded anymore')
                self._flood_start[conversation] = 0
                self._flood_count[conversation] = 0
                return text
            else:
                # We're still flooded
                return None
      
        if t - self._flood_time > self._time:
            self._flood_time = t

            if self._flood_count[conversation] > self._count:
                self._flood_count[conversation] = 0
                self._flood_start[conversation] = t
                self.report('Flood start at {}'.format(t))
                reply_func(conversation, 'Flood! 😬')
                return None

            self._flood_count[conversation] = 0

        return text


ADDON[_NAME] = _FloodAddon
