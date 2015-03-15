# -*- coding: utf-8 -*-

'''
Karma Manager

This addon parses karma commands and keeps the chat karma counter
'''

from ..addon import Addon, ADDON
from ..database import Database


_NAME = "karma"


class _KarmaDatabase(Database):

    def __init__(self, dbfile):
        super().__init__(dbfile)

    def create_table(self):
        if not self.table_exists('karma'):
            self.cursor.execute('CREATE TABLE karma(name VARCHAR(30) PRIMARY KEY, total INTEGER);')
            self.conn.commit()

    def insert_karma(self, name, total):
        try:
            self.cursor.execute("INSERT INTO karma(name, total) VALUES ('%s', %d );" % (name, total))
            self.conn.commit()
            return True
        except:
            return False

    def change_karma(self, name, amount):
        if not self.insert_karma(name, amount):
            self.cursor.execute("UPDATE karma SET total = total + (%d) where name = '%s';" % (amount, name))
            self.conn.commit()

    def increment_karma(self, name):
        return self.change_karma(name, 1)

    def decrement_karma(self, name):
        return self.change_karma(name, -1)

    def get_karmas_count(self, desc=True, max_len=400):
        q = 'SELECT name, total FROM karma order by total'
        if desc:
            q += ' desc'
        self.cursor.execute(q)
        karmas = ''
        for l in self.cursor:
            item = (l[0]) + ' = ' + str(l[1])
            if len(karmas) == 0:
                append = item
            else:
                append = ', ' + item
            if len(karmas) + len(append) > max_len:
                break
            karmas += append

        return karmas

    def get_karmas(self):
        self.cursor.execute('SELECT name FROM karma order by total desc')
        karmas = ''
        for l in self.cursor:
            if len(karmas) == 0:
                karmas = (l[0])
            else:   
                karmas = karmas + ', ' + (l[0])

        return karmas

    def get_karma(self, name):
        self.cursor.execute("SELECT total FROM karma where name = '%s'" % (name))
        for l in self.cursor:
                return (l[0])


class _KarmaAddon(Addon):

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _KarmaDatabase(self._dbfile)
        self._db.create_table()

    def get_parsers(self):
        return [
            (r'\b(\w(\w|[._-])+)\+\+', self._do_karma),
            (r'\b(\w(\w|[._-])+)\-\-', self._do_dec_karma),
            (r'^@*karma (\w+) *$', self._do_show_karma),
            (r'^@*karmas', self._do_dump_karmas)
        ]

    def _do_karma(self, conversation, from_user, match, reply):
        """Increment karma"""
        var = match.group(1).lower()
        if from_user.first_name.lower() == var:
            reply(conversation, "%s, convencido!" % from_user.first_name)
            return

        self._db.increment_karma(var)

        if var.lower() == self._bot_name:
            reply(conversation, 'eu sou foda! ' + str(self._db.get_karma(var)) + ' pontos de karma')
        else:
            reply(conversation, var + ' agora tem ' + str(self._db.get_karma(var)) + ' pontos de karma')

    def _do_dec_karma(self, conversation, from_user, match, reply):
        """Decrement karma"""
        var = match.group(1).lower()
        if from_user.first_name.lower() == var:
            reply(conversation, u"%s, tadinho... vem cá e me dá um abraço!" % from_user.first_name)
            return
        
        self._db.decrement_karma(var)
    
        if var.lower() == self._bot_name:
            reply(conversation, 'tenho ' + str(self._db.get_karma(var)) + ' pontos de karma agora  :(')
        else:
            reply(conversation, var + ' agora tem ' + str(self._db.get_karma(var)) + ' pontos de karma')

    def _do_show_karma(self, conversation, from_user, match, reply):
        """Show karma of a specific name"""
        var = match.group(1).lower()
        points = self._db.get_karma(var)
        if points is not None:
            reply(conversation, var + ' tem ' + str(points) + ' pontos de karma')
        else:
            reply(conversation, var + " não tem nenhum ponto de karma")

    def _do_dump_karmas(self, conversation, from_user, match, reply):
        """Show high and low karmas"""
        reply(conversation, '[+] karmas: ' + self._db.get_karmas_count(True))
        reply(conversation, '[-] karmas: ' + self._db.get_karmas_count(False))



ADDON[_NAME] = _KarmaAddon

