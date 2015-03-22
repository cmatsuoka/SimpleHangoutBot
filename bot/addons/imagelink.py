# -*- coding: utf-8 -*-

'''
Image link poster

This addon parses images links and posts them to the chat window
'''

import mimetypes
import tempfile
import os

from PIL import Image as image
from requests import get
from shutil import copyfileobj

from ..addon import Addon, ADDON
from ..database import Database

_NAME = 'imagelink'

# will ignore images bigger than 5MB
_PAYLOAD_LIMIT = 5000000


class _ImageLinkAddon(Addon):

    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

        mimetypes.init()
        self._extensions = []
        for ext in mimetypes.types_map:
            if 'image' in mimetypes.types_map[ext]:
                self._extensions.append(ext.replace('.', ''))
        self.report("List of known image extensions: {}".format(' '.join(self._extensions)))

    def get_filters(self):
        return [self._check_match]

    def _check_match(self, conversation, user, link, reply):
        """Checks if the message contains an image link"""

        self.report("Checking match {}".format(link))
        if link.lower().endswith(tuple(self._extensions)) and not user.is_self:
            self.report("{} posted a valid image link {}".format(user.first_name, link))
            self._do_post_image(conversation, reply, link)

        return link

    def _do_post_image(self, conversation, reply, link):
        """Posts the locally saved image to the conversation"""

        # FIXME: missing image posting code here
        # (currently not implemented in hangups)
        filename = self._do_fetch_image(link)
        if filename:
            filesize = image.open(filename).size
            reply(conversation, "Se hangups suportasse imagens eu poderia embutir esse {} de {} pixels aqui :-(".format(filename, filesize))
        else:
            reply(conversation, "Deu pau pra abrir essa imagem...")

        return True

    def _do_fetch_image(self, link):
        """Save the image link to a temp file so it can be posted"""
        req = None

        try:
            req = get(link, stream=True, timeout=5)
            self.report("Request returned: {}".format(req.status_code))
        except Exception as e:
            self.report("Failed to get image data: {}".format(e))
            return None

        if not req.ok:
            self.report("Something else went wrong...")
            return None

        if not 'image' in req.headers.get('Content-Type'):
            self.report("Not a real image link")
            return None

        payload = req.headers.get('Content-Length')
        if payload is None:
            self.report("Payload is None!")
            return None

        self.report("Payload to fetch: {}".format(payload))

        if int(payload) > _PAYLOAD_LIMIT:
            self.report("Payload of {} is bigger than the {} bytes limit!".format(payload, _PAYLOAD_LIMIT))
            return None

        filepath = os.path.join('/tmp/', link.split('/')[-1])
        with open(filepath, 'wb') as fileobj:
            self.report("Writing image {} to post it to the conversation".format(filepath))
            req.raw.decode_content = True
            copyfileobj(req.raw, fileobj)
        return filepath


ADDON[_NAME] = _ImageLinkAddon
