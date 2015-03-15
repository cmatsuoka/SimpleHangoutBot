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

    def __init__(self, addon):
        super().__init__(addon)

    def get_digest(self, conversation, user):
        result = self.query("SELECT text FROM hashtag WHERE conversation='{}' AND user='{}';".format(conversation, user))
        for l in result:
            yield l[0]


class _DigestAddon(Addon):

    version = '(dev)'
    requires = [ 'hashtag' ]

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)
        self._db = _DigestDatabase(self)

    def get_parsers(self):
        return [
            (r'^digest$', self._do_daily_digest)
        ]

    def _do_daily_digest(self, conversation, from_user, match, reply):
        """List tagged texts"""
        self.report("list hashtags")
        for i in self._db.get_digest(conversation.id_, from_user.id_.chat_id):
            self._send_user_message(from_user.id_.chat_id, i)


ADDON[_NAME] = _DigestAddon

