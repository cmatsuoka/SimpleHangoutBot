# -*- coding: utf-8 -*-

'''
Learn

Like responder, but based on a dynamically generated list
'''

from ..addon import Addon, ADDON
from ..database import Database
import re
import time


_NAME = 'learn'


class _LearnDatabase(Database):

    def __init__(self, addon):
        super().__init__(addon)

    def create_table(self):
        try:
            if not self.table_exists('learn'):
                self.query('CREATE TABLE learn(name VARCHAR PRIMARY KEY, conversation VARCHAR, pattern VARCHAR, reply VARCHAR);')
                self.commit()
            return True
        except:
            return False

    def insert(self, name, conversation_id, pattern, reply):
        try:
            self.query("INSERT INTO learn(name, conversation, pattern, reply) VALUES ('{}','{}','{}','{}');".format(name, conversation_id, pattern, reply))
            self.commit()
            return True
        except:
            return False

    def delete(self, name, conversation_id):
        try:
            result = self.query("DELETE FROM learn WHERE name='{}' AND conversation='{}';".format(name,conversation_id))
            return True
        except:
            return False

    def retrieve(self):
        try:
            result = self.query("SELECT conversation,pattern,reply FROM learn;")
            ret = [ ]
            for l in result:
                ret.append(l)
            return ret
        except:
            self.report('Retrieval error.')
            return [ ]


class _LearnAddon(Addon):

    version = '(dev)'

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _LearnDatabase(self)
        self._db.create_table()
        self._knowledge = self._db.retrieve()

    def get_parsers(self):
        return [
            (r'^/learn help\s*$', self._do_learn_help),
            (r'^/learn delete\s+(\w+)\s*$', self._do_learn_delete),
            (r'^/learn\s+(\w+)\s+/(.*)/\s+(.*)\s*$', self._do_learn),
            (r'^/learn', self._do_learn_help)
        ]

    def get_filters(self):
        return [
            self._responder
        ]

    def _responder(self, conversation, user, text, reply_func):
        if text is not None:
            try:
                for k in self._knowledge:
                    conv = k[0]
                    pattern = k[1]
                    reply = k[2]
                    for match in re.finditer(pattern, text):
                        self.report("Pattern match: '{}'".format(match.group()))
                        reply_func(conversation, reply)
            except Exception as e:
                self.report('Error handling msg: {}'.format(e))
        return text

    def _do_learn(self, conversation, from_user, match, reply):
        name = match.group(1)
        regexp = match.group(2)
        myreply = match.group(3)
        self.report('learn {} /{}/ -> {}'.format(name, regexp, myreply))
        self._db.insert(name, conversation.id_, regexp, myreply)
        self._knowledge = self._db.retrieve()
        reply(conversation, 'Ok.')
        return True

    def _do_learn_delete(self, conversation, from_user, match, reply):
        name = match.group(1)
        self._db.delete(name, conversation.id_)
        return True

    def _do_learn_help(self, conversation, from_user, match, reply):
        reply(conversation, '/learn name /regexp/ reply')
        reply(conversation, '/learn delete name')
        reply(conversation, 'Special vars: $ME $YOU $CONV $1, $2...')
        return True

ADDON[_NAME] = _LearnAddon

