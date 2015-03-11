# -*- coding: utf-8 -*-

import os
import sqlite3

class Database(object):
    def __init__(self, dbfile):
        if not os.path.exists(dbfile):
            self.conn = sqlite3.connect(dbfile)
            self.cursor = self.conn.cursor()
            self.create_table()

        self.conn = sqlite3.connect(dbfile)
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def table_exists(self, name):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s'" % (name))
        for l in self.cursor:
            return len(l) > 0

