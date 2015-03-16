# -*- coding: utf-8 -*-

'''
Learn

Like responder, but based on a dynamically generated list
'''

from ..addon import Addon, ADDON
from ..database import Database
import re
import time
from hangups.user import UserID


_NAME = 'learn'


class _LearnDatabase(Database):

    def __init__(self, addon):
        super().__init__(addon)

    def create_table(self):
        try:
            if not self.table_exists('learn'):
                self.query('CREATE TABLE learn(name VARCHAR PRIMARY KEY, conversation VARCHAR, chat_id VARCHAR, gaia_id VARCHAR, time INTEGER, pattern VARCHAR, reply VARCHAR);')
                self.commit()
            return True
        except:
            return False

    def exists(self, name, conversation_id):
        try:
            if conversation_id is None:
                result = self.query("SELECT COUNT(name) FROM learn WHERE name='{}';".format(name))
            else:
                result = self.query("SELECT COUNT(name) FROM learn WHERE name='{}' AND conversation='{}';".format(name, conversation_id))

            for l in result:
                return int(l[0]) > 0
        except:
            return False
            

    def insert(self, name, conversation_id, user_id, time, pattern, reply):
        try:
            self.query("INSERT INTO learn(name, conversation, chat_id, gaia_id, time, pattern, reply) VALUES ('{}','{}','{}','{}',{},'{}','{}');".format(name, conversation_id, user_id.chat_id, user_id.gaia_id, time, pattern, reply))
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

    def list_names(self, conversation_id):
        if conversation_id is None:
            result = self.query("SELECT name FROM learn;")
        else:
            result = self.query("SELECT name FROM learn WHERE conversation='{}';".format(conversation_id))
        names = ''
        for l in result:
            names += ' ' + l[0]
        return names

    def show(self, name, conversation_id):
        if conversation_id is None:
            result = self.query("SELECT pattern,reply FROM learn WHERE name='{}';".format(name))
        else:
            result = self.query("SELECT pattern,reply FROM learn WHERE name='{}' AND conversation='{}';".format(name, conversation_id))
        for l in result:
            return (l[0], l[1])
        return None

    def show_author(self, name, conversation_id):
        if conversation_id is None:
            result = self.query("SELECT chat_id,gaia_id,time FROM learn WHERE name='{}';".format(name))
        else:
            result = self.query("SELECT chat_id,gaia_id,time FROM learn WHERE name='{}' AND conversation='{}';".format(name, conversation_id))
        for l in result:
            return (l[0], l[1], l[2])
        return None

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

    version = '0.1'

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _LearnDatabase(self)
        self._db.create_table()
        self._knowledge = self._db.retrieve()

	# Configuration

        s = _NAME.capitalize()
        if config.has_options(s, [ 'isolation' ]):
            self._isolation = config.getboolean(s, 'isolation')
        else:
            config.add_option(s, 'isolation', 'True')

    def get_parsers(self):
        return [
            (r'^/learn help\s*$', self._do_learn_help),
            (r'^/learn list', self._do_learn_list),
            (r'^/learn blame\s+(\w+)\s*$', self._do_learn_blame),
            (r'^/learn show\s+(\w+)\s*$', self._do_learn_show),
            (r'^/learn forget\s+(\w+)\s*$', self._do_learn_forget),
            (r'^/learn\s+(\w+)\s+/(.*)/\s+(.*)\s*$', self._do_learn),
            (r'^/learn', self._do_learn_help)
        ]

    def get_filters(self):
        return [
            self._responder
        ]

    def _responder(self, conversation, user, text, reply_func):
        if text.startswith('/') or user.is_self:
            return text

        try:
            for k in self._knowledge:
                conv = k[0]
                pattern = k[1]
                reply = k[2]

                if self._isolation and conversation.id_ != conv:
                    continue

                regex = re.compile(pattern)
                match = regex.search(text)
                if match:
                    self.report("Pattern match: '{}'".format(match.group()))
                    reply = reply.replace('$ME', self.bot_name)
                    reply = reply.replace('$YOU', user.first_name)
                    for i in range(1, regex.groups + 1):
                        reply = reply.replace('$' + str(i), match.group(i))
                    reply_func(conversation, reply)
        except Exception as e:
            self.report('Error handling msg: {}'.format(e))

        return text

    def _do_learn(self, conversation, from_user, match, reply):
        name = match.group(1)
        pattern = match.group(2)
        myreply = match.group(3)

        if self._db.exists(name, None):
            self.report('Attempt to redefine ' + name)
            reply(conversation, 'Redefine.')
            return True

        self.report('learn {} /{}/ -> {}'.format(name, pattern, myreply))
        self._db.insert(name, conversation.id_, from_user.id_, int(time.time()), pattern, myreply)
        self._knowledge = self._db.retrieve()
        reply(conversation, 'Ok.')
        return True

    def _do_learn_list(self, conversation, from_user, match, reply):
        if self._isolation:
            conv = conversation.id_
        else:
            conv = None
        reply(conversation, self._db.list_names(conv))
        return True

    def _do_learn_show(self, conversation, from_user, match, reply):
        if self._isolation:
            conv = conversation.id_
        else:
            conv = None
        name = match.group(1)
        val = self._db.show(name, conv)
        if val is not None:
            reply(conversation, '{}: /{}/ -> {}'.format(name, val[0], val[1]))
        else:
            reply(conversation, 'Error.')
        return True

    def _do_learn_blame(self, conversation, from_user, match, reply):
        if self._isolation:
            conv = conversation.id_
        else:
            conv = None
        name = match.group(1)

        if not self._db.exists(name, conversation.id_):
            reply(conversation, '{}?'.format(name))
            return True

        val = self._db.show_author(name, conv)

        if val is not None:
            userid = UserID(chat_id=val[0], gaia_id=val[1])
            user = self._user_list.get_user(userid)
            if user is not None:
                date = time.strftime('%x', time.localtime(val[2]))
                reply(conversation, '{}, {}'.format(user.first_name, date))
                return True

        reply(conversation, 'unknown')
        return True

    def _do_learn_forget(self, conversation, from_user, match, reply):
        name = match.group(1)
        self._db.delete(name, conversation.id_)
        return True

    def _do_learn_help(self, conversation, from_user, match, reply):
        reply(conversation, '/learn name /regexp/ reply')
        reply(conversation, '/learn forget name')
        reply(conversation, 'Special vars: $ME $YOU $1, $2...')
        return True

ADDON[_NAME] = _LearnAddon

