# -*- coding: utf-8 -*-

'''
Private message forwarder

This addon forward group chat messages to users in private based on predefined keywords
'''

from ..addon import Addon, ADDON
from ..database import Database
from datetime import datetime


_NAME = 'pvtme'


class _PvtMeDatabase(Database):

    def __init__(self, addon):
        super().__init__(addon)

    def create_table(self):
        if not self.table_exists('pvtme'):
            self.query('CREATE TABLE pvtme(user_id VARCHAR(128), conversation_id VARCHAR(128), keywords VARCHAR(512));')
            self.commit()

    def clear_keywords(self, user_id, conversation_id):
        try:
            self.query("DELETE FROM pvtme WHERE (user_id = '%s' and conversation_id = '%s');" % (user_id, conversation_id))
            self.commit()
            return True
        except:
            return False

    def insert_keywords(self, user_id, conversation_id, keywords):
        if (not keywords or keywords == ""):
            return False

        try:
            # drop old keywords first
            self.clear_keywords(user_id, conversation_id)
            self.query("INSERT INTO pvtme(user_id, conversation_id, keywords) VALUES ('%s', '%s', '%s' );" % (user_id, conversation_id, keywords))
            self.commit()
            return True
        except:
            return False

    def get_keywords(self, user_id, conversation_id):
        try:
            result = self.query("SELECT keywords FROM pvtme WHERE (user_id='%s' AND conversation_id='%s');" % (user_id, conversation_id))
            for l in result:
                return l[0]
            return None
        except:
            return None

    def get_keywords_for_conversation(self, conversation_id):
        try:
            list_of_keywords = {}
            result = self.query("SELECT user_id,keywords FROM pvtme WHERE (conversation_id='%s');" % (conversation_id))
            for l in result:
                list_of_keywords[l[0]] = l[1]
            return list_of_keywords
        except:
            return {}


class _PvtMeAddon(Addon):

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _PvtMeDatabase(self)
        self._db.create_table()

    def get_parsers(self):
        return [
            (r'^/pvtme set (.*)$', self._set_keywords),
            (r'^/pvtme dump$', self._dump_keywords),
            (r'^/pvtme clear$', self._clear_keywords),
            (r'^/pvtme help$', self._show_help),
        ]

    def get_filters(self):
        return [ self._check_match ]

    def _check_match(self, conversation, user, text, reply_func):
        if text.startswith("/pvtme") or user.is_self:
            return text

        keywords = self._db.get_keywords_for_conversation(conversation.id_)
        for user_id in keywords:
            if user_id == user.id_.chat_id:
                continue
            for keyword in keywords[user_id].split(","):
                if (text.rfind(keyword) != -1):
                    self.report('found keyword')
                    self._send_user_message(user_id,'({}) - {}: {}'.format(datetime.now().strftime('%d/%m %I:%M%p'), user.first_name, text))

                    break
        return text

    def _set_keywords(self, conversation, from_user, match, reply):
        keywords = match.group(1).lower()
        self.report('set keyword: ' + keywords)
        if (self._db.insert_keywords(from_user.id_.chat_id, conversation.id_, keywords)):
            reply(conversation, "Tá bom, {}. Eu te aviso".format(from_user.first_name))
        else:
            reply(conversation, "Não vou poder te avisar, {}! Desculpe-me :(".format(from_user.first_name))

    def _dump_keywords(self, conversation, from_user, match, reply):
        self.report('dump keywords')
        res = self._db.get_keywords(from_user.id_.chat_id, conversation.id_)
        if not res:
            reply(conversation, "Não achei nada aqui para você, {}.".format(from_user.first_name))
        else:
            reply(conversation, "Keywords para {}: {}".format(from_user.first_name, res))

    def _clear_keywords(self, conversation, from_user, match, reply):
        self.report('clear keywords')
        if(self._db.clear_keywords(from_user.id_.chat_id, conversation.id_)):
            reply(conversation, "Tá bom, não te incomodo mais!")
        else:
            reply(conversation, "Não consegui limpar as keywords :(")

    def _show_help(self, conversation, from_user, match, reply):
        reply(conversation, "Uso: /pvtme (set,clear,dump) [keyword,keyword2]")


ADDON[_NAME] = _PvtMeAddon

