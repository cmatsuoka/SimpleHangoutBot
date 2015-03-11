# -*- coding: utf-8 -*-

import re

class Addon(object):
    ADDON_TYPE_PARSE = 0
    ADDON_TYPE_TIMER = 1
    ADDON_TYPE_IDLE  = 2

    def __init__(self, config, name):
        if name != None:
            self.name = name
        self._data = ()
        self._config = config

    def get_res_list(self):
        raise NotImplementedError

class ParseAddon(Addon):
    def __init__(self, config, name):
        super().__init__(config, name)
        self._type = self.ADDON_TYPE_PARSE

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

