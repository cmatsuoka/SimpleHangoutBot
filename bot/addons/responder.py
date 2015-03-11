# -*- coding: utf-8 -*-

'''
Basic responder

This addon parses key strings and replies accordingly
'''

from ..addon import ParseAddon, ADDON


_NAME = 'responder'


class _ResponderAddon(ParseAddon):
    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

    def get_res_list(self):
        return [
            ('^ping\?*$', lambda c,f,m,reply: reply(c, 'pong!')),
            (r'^hey[?!.]*$', lambda c,f,m,reply: reply(c, u'ho!')),
        ]


ADDON[_NAME] = _ResponderAddon

