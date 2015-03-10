# -*- coding: utf-8 -*-

import re

class Addon(object):
    def __init__(self, config, name):
        if name != None:
            self.name = name
        self._data = ()
        self._config = config

    def re_list(self, l):
        """Return a list with functions for compiled regex"""
        return [(re.compile(r, re.UNICODE), fn) for (r, fn) in l]


ADDON = { }

def all():
    return ADDON.keys()

def _init(label, config):
    return ADDON[label](config)

def addons(config):
    ret = [ _init(i, config) for i in config.getlist('Global', 'addons') ]
    if config.changed():
        config.write()
    return ret

