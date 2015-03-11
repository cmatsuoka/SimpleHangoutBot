# -*- coding: utf-8 -*-

'''
Basic responder

This addon parses key strings and replies accordingly
'''

from ..addon import ParseAddon, ADDON


_NAME = 'responder'


class _ResponderAddon(ParseAddon):
    def __init__(self, config, name=_NAME):
        super().__init__(config, name)

    def get_res_list(self):
        return [
            (r'^ *tu[ -]*dum[\.!]*$''', lambda c,f,m,reply: reply(c, u'PÁ!')),
            (u'(?i)^o* *meu +pai +(é|e)h* +detetive[\.!]*$', lambda c,f,m,reply: reply(c, u'mas o teu é despachante')),
            (u'(?i)ningu[ée]m f(a|e)z nada!', lambda c,f,m,reply: reply(c, u'ninguém f%sz nada! NA-DA!' % (m.group(1)))),
            (r'(?i)\b(bot|carcereiro) burro', lambda c,f,m,reply: reply(c, ":'(")),
            (u'(?i)\\bo +m[aá]rio\\b', lambda c,f,m,reply: reply(c, u'que mario?')),
            (u'(?i)^(oi|ol[áa])\\b', lambda c,f,m,reply: reply(c,u'oi, tudo bem?')),
            (u'^(tudo|td) bem[.,]* e* *(vc|voc[eê])[?!.]*$', lambda c,f,m,reply: reply(c, u'tudo bem também')),
            (r'\b(tudo|td) bem\?$', lambda c,f,m,reply: reply(c, u'tudo bem. e você?')),
            (r'\btudo bem[.!]*$', lambda c,f,m,reply: reply(c, u'que bom, então')),
            (r'^hey[?!.]*$', lambda c,f,m,reply: reply(c, u'ho!')),
            ('^ping\?*$', lambda c,f,m,reply: reply(c, 'pong!')),
            (u'^sim[, ]+(vc|voc[eê])', lambda c,f,m,reply: reply(c, u'eu não!')),
            (r':(\*+)', lambda c,f,m,reply: reply(c, u':%s' % (m.group(1)))),
            (r'(?i)\b(bot|carcereiro) te (amo|adoro|odeio)', lambda c,f,m,reply: reply(c, u'eu também te %s!' % (m.group(2)))),
            (r'(?i)\b(nazi|hitler\b)', lambda c,f,m,reply: reply(c, u'Godwin! a discussão acabou, você perdeu.')),
            ('carcereiro|carcy', lambda c,f,m,reply: reply(c, u'eu?'))
        ]


ADDON[_NAME] = _ResponderAddon

