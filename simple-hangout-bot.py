#!/usr/bin/env python3

import appdirs
import argparse
import asyncio
import hangups
import os
import re
import signal
import sqlite3
import sys
import time


class SQLiteDB():
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

    def create_table(self):
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

class SimpleHangoutBot(object):
    """Bot main class"""
    def __init__(self, cookies_path, max_retries=5):
        self._client = None
        self._cookies_path = cookies_path
        self._max_retries = max_retries

        # These are populated by on_connect when it's called.
        self._conv_list = None # hangups.ConversationList
        self._user_list = None # hangups.UserList

        # Database to store bot data
        self._db = SQLiteDB('carcereiro.db')

        # List with handled msgs.
        self._res_list = self._re_list([
            (r'\b(\w(\w|[._-])+)\+\+', self._do_karma),
            (r'\b(\w(\w|[._-])+)\-\-', self._do_dec_karma),

            (r'^@*karma (\w+) *$', self._do_show_karma),
            (r'^@*karmas', self._do_dump_karmas),

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
        ])

        # Handle signals
        try:
            loop = asyncio.get_event_loop()
            for signum in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(signum, lambda: self.stop())
        except NotImplementedError:
            pass

    def login(self, cookies_path):
        """Login to Google account"""
        # Authenticate Google user and save auth cookies
        # (or load already saved cookies)
        try:
            cookies = hangups.auth.get_auth_stdin(cookies_path)
            return cookies
        except hangups.GoogleAuthError as e:
            print('Login failed ({})'.format(e))
            return False

    def run(self):
        """Connect to Hangouts and run bot"""
        cookies = self.login(self._cookies_path)
        if cookies:
            # Create Hangups client
            self._client = hangups.Client(cookies)
            self._client.on_connect.add_observer(self._on_connect)
            self._client.on_disconnect.add_observer(self._on_disconnect)

            # If we are forcefully disconnected, try connecting again
            loop = asyncio.get_event_loop()
            for retry in range(self._max_retries):
                try:
                    loop.run_until_complete(self._client.connect())
                    sys.exit(0)
                except Exception as e:
                    print('Client disconnected: {}'.format(e))
                    print('Connecting again ({} of {})'.format(retry + 1, self._max_retries))
                    time.sleep(5 + retry * 5)
            print('Exiting!')
        sys.exit(1)

    def stop(self):
        """Disconnect from Hangouts"""
        asyncio.async(
            self._client.disconnect()
        ).add_done_callback(lambda future: future.result())

    def handle_chat_event(self, conv_event):
        """Handle chat event"""
        conversation = self._conv_list.get(conv_event.conversation_id)
        user = conversation.get_user(conv_event.user_id)

        # Don't handle events caused by the bot himself
        if user.is_self:
            return
        
        self.handle_msg(conversation, user, conv_event.text, self.send_message)

    def handle_msg(self, conversation, user, text, reply_func):
        try:
            for r,fn in self._res_list:
                match = r.search(text)
                if match:
                    r = fn(conversation, user, match, reply_func)
                    if not r:
                        return r
            return True
        except Exception as e:
            print('Error handling msg: {}'.format(e))

    def send_message(self, conversation, msg):
        """Send chat message"""
        segments = [hangups.ChatMessageSegment(msg)]
        self.send_message_segments(conversation, segments)

    def send_message_segments(self, conversation, segments):
        """Send chat message segments"""
        # Ignore if the user hasn't typed a message.
        if len(segments) == 0:
            return
        asyncio.async(
            conversation.send_message(segments)
        ).add_done_callback(self._on_message_sent)

    def _on_connect(self, initial_data):
        """Handle connecting for the first time"""
        self._user_list = hangups.UserList(self._client,
                                           initial_data.self_entity,
                                           initial_data.entities,
                                           initial_data.conversation_participants)

        self._conv_list = hangups.ConversationList(self._client,
                                                   initial_data.conversation_states,
                                                   self._user_list,
                                                   initial_data.sync_timestamp)
        self._conv_list.on_event.add_observer(self._on_event)
        print('Connected!')

    def _on_disconnect(self):
        """Handle disconnecting"""
        print('Disconnected!')

    def _on_event(self, conv_event):
        """Handle conversation events"""
        if isinstance(conv_event, hangups.ChatMessageEvent):
            self.handle_chat_event(conv_event)

    def _on_message_sent(self, future):
        """Handle showing an error if a message fails to send"""
        try:
            future.result()
        except hangups.NetworkError:
            print('Failed to send message!')

    def _re_list(self, l):
        """Return a list with functions for compiled regex"""
        return [(re.compile(r, re.UNICODE), fn) for (r, fn) in l]

    def _do_karma(self, conversation, from_user, match, reply):
        """Increment karma"""
        var = match.group(1).lower()
        if from_user.first_name.lower() == var:
            reply(conversation, "%s, convencido!" % from_user.first_name)
            return

        self._db.increment_karma(var)

        if var.lower() == 'carcereiro':
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
    
        if var.lower() == 'carcereiro':
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

def main():
    """Main function"""
    # Build default paths for files.
    dirs = appdirs.AppDirs('simple-hangout-bot', 'simple-hangout-bot')
    default_cookies_path = os.path.join(dirs.user_data_dir, 'cookies.json')

    # Configure argument parser
    parser = argparse.ArgumentParser(prog='simple-hangout-bot',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--cookies', default=default_cookies_path,
                        help='cookie storage path')
    args = parser.parse_args()

    # Create necessary directories.
    for path in [args.cookies]:
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                sys.exit('Failed to create directory: {}'.format(e))

    # Run, Bot, Run 
    bot = SimpleHangoutBot(args.cookies)
    bot.run() 

if __name__ == '__main__':
    print(main())
