# -*- coding: utf-8 -*-

import os
import sqlite3

class Database(object):
    def __init__(self, addon):
        self._addon = addon
        self._conn = sqlite3.connect(addon.dbfile)
        self._cursor = self._conn.cursor()

    def close(self):
        self._cursor.close()
        self._conn.close()

    def table_exists(self, name):
        self._cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='%s'" % (name))
        for l in self._cursor:
            return int(l[0]) > 0

    def query(self, q):
        try:
            self._cursor.execute(q)
            return self._cursor
        except sqlite3.Error as e:
            self.report(e)
            raise e

    def commit(self):
        try:
            self._conn.commit()
        except sqlite3.Error as e:
            self.report(e)
            raise e

    def report(self, text):
        self._addon.report('Database: ' + text)
