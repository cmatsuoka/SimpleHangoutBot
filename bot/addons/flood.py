# -*- coding: utf-8 -*-

'''
Flood control

This filter addon halts bot response if a flood is detected
'''

import time

from ..addon import Addon, ADDON


_NAME = 'flood'


class _FloodAddon(Addon):
    _FLOOD_COUNT = 2

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

        self._flood_count = { }
        self._flood_start = { }
        self._flood_time = 0


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
            if t - self._flood_start[conversation] > 5:
                # End of flood control
                self._flood_start[conversation] = 0
                return text
            else:
                # We're still flooded
                return None

        print(t, self._flood_time)

        if t - self._flood_time > 2:
            self._flood_time = t

            if self._flood_count[conversation] > self._FLOOD_COUNT:
                self._flood_count[conversation] = 0
                self._flood_start[conversation] = t
                reply_func(conversation, 'Flood! 😬')
                return None

            self._flood_count[conversation] = 0

        return text


ADDON[_NAME] = _FloodAddon
