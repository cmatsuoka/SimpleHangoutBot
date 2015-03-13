# -*- coding: utf-8 -*-

class Addon(object):
    author = ''
    version = ''
    requires = [ ]

    def __init__(self, config, name):
        if name != None:
            self.name = name
        self._data = ()
        self._config = config

    def get_parsers(self):
        return [ ]

    def get_filters(self):
        return [ ]

    def get_timers(self):
        return [ ]

    # Low-level hooks

    def set_client(self, client):
        pass

    def on_connect(self, initial_data):
        pass

    def on_event(self, conv_event):
        pass

    def on_disconnect(self):
        pass

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

