# -*- coding: utf-8 -*-

'''
Digest Manager

This addon retrieves items from the hashtag database
'''

from ..addon import Addon, ADDON
from ..database import Database
import time


_NAME = 'digest'

# TODO:
# digest subscribe <email>
# digest unsubscribe
# scheduled digest

class _DigestDatabase(Database):

    def __init__(self, dbfile):
        super().__init__(dbfile)

    def get_digest(self, conversation, user):
        self.cursor.execute("SELECT text FROM hashtag WHERE conversation='{}' AND user='{}';".format(conversation, user))
        for l in self.cursor:
            yield l[0]


class _DigestAddon(Addon):

    requires = [ 'hashtag' ]

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _DigestDatabase(self._dbfile)

    def get_parsers(self):
        return [
            (r'^digest$', self._do_daily_digest)
        ]

    def _do_daily_digest(self, conversation, from_user, match, reply):
        """List tagged texts"""
        self._report("list hashtags")
        for i in self._db.get_digest(conversation.id_, from_user.id_.chat_id):
            self._send_user_message(from_user.id_.chat_id, i)


ADDON[_NAME] = _DigestAddon

