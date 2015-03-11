# -*- coding: utf-8 -*-

'''
Basic responder

This addon parses key strings and replies accordingly
'''

from ..addon import Addon, ADDON


_NAME = 'responder'


class _ResponderAddon(Addon):
    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

    def get_parsers(self):
        return [
            ('^ping\?*$', lambda c,f,m,reply: reply(c, 'pong!')),
            (r'^hey[?!.]*$', lambda c,f,m,reply: reply(c, u'ho!')),
        ]


ADDON[_NAME] = _ResponderAddon

