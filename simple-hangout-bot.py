#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SimpleHangoutBot

A Simple Hangout Bot based on Hangups
"""

import os
import re
import sys
import time
import signal
import asyncio
import hangups
import argparse

import bot.config
import bot.addon
from bot.addons import *
from bot.util import *

class SimpleHangoutBot(object):
    """Bot main class"""
    def __init__(self, config):
        self._client = None
        self._name = config.get('Global', 'name')
        self._db = config.get('Global', 'dbfile')
        self._cookies_path = config.get('Global', 'cookies')

        report('                     ')
        report('     ((  o  ))       ')
        report('         |           ')
        report('     .---T---.       ')
        report('   -{  O   o  }-     Simple Hangout Bot')
        report('     `-.+++.-\'       written by 404')
        report('         H           ')
        report('   o==##[=]##==o     Name    : {}'.format(self._name))
        report('   H   #####   H     Cookies : {}'.format(self._cookies_path))
        report('  (T)   H H   (T)    Database: {}'.format(self._db))
        report('        H H          ')
        report('       ## ##         ')
        report('                     ')

        # These are populated by on_connect when it's called.
        self._user_list = None # hangups.UserList
        self._conv_list = None # hangups.ConversationList

        # Our add-ons
        self._addons = bot.addon.addons(config)

        # List with handled msgs.
        self._parsers = [ ]
        self._filters = [ ]

        for addon in self._addons:
            self._parsers += self._re_list(addon.get_parsers())
            self._filters += addon.get_filters()

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
            report('Login failed ({})'.format(e))
            return False

    def run(self):
        """Connect to Hangouts and run bot"""
        cookies = self.login(self._cookies_path)
        if cookies:
            # Create Hangups client
            self._client = hangups.Client(cookies)
            self._client.on_connect.add_observer(self._on_connect)
            self._client.on_disconnect.add_observer(self._on_disconnect)

            for addon in self._addons:
                addon.set_client(self._client)

            # If we are forcefully disconnected, try connecting again
            loop = asyncio.get_event_loop()
            tries = 0
            while True:
                tries += 1
                try:
                    loop.run_until_complete(self._client.connect())
                    sys.exit(0)
                except Exception as e:
                    report('Client disconnected: {}'.format(e))
                    wait = tries * 5
                    if wait > 300:
                        wait = 300
                    time.sleep(wait)
                    report('Connecting again ({})'.format(tries))

            report('Exiting!')
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
	
        if conversation.name is None:
           conv_name = conv_event.conversation_id
        else:
           conv_name = conversation.name

        report('{}:{}> {}'.format(conv_name[:7], user.first_name[:7].ljust(7),
                                  conv_event.text))

        text = conv_event.text

        # Apply filter addons
        for f in self._filters:
            text = f(conversation, user, text, self.send_message)
            if text is None:
                return

        # Don't handle events caused by the bot himself
        if user.is_self:
            return
        
        self.handle_msg(conversation, user, text, self.send_message)

    def handle_msg(self, conversation, user, text, reply_func):
        if text is not None:
            try:
                for r,fn in self._parsers:
                    for match in re.finditer(r,text):
                        report("Pattern match: '{}'".format(match.group()))
                        ret = fn(conversation, user, match, reply_func)
                        if ret is True:
                            report('Input consumed')
                            return ret
                return False 
            except Exception as e:
                report('Error handling msg: {}'.format(e))

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

        for addon in self._addons:
            addon.on_connect(initial_data, self._user_list, self._conv_list)

        report('Connected!')

    def _on_disconnect(self):
        """Handle disconnecting"""

        for addon in self._addons:
            addon.on_disconnect()

        self._conv_list.on_event.remove_observer(self._on_event)

        report('Disconnected!')

    def _on_event(self, conv_event):
        """Handle conversation events"""

        for addon in self._addons:
            addon.on_event(conv_event)

        if isinstance(conv_event, hangups.ChatMessageEvent):
            self.handle_chat_event(conv_event)

    def _on_message_sent(self, future):
        """Handle showing an error if a message fails to send"""
        try:
            future.result()
        except hangups.NetworkError:
            report('Failed to send message!')

    def _re_list(self, l):
        """Return a list with functions for compiled regex"""
        return [(re.compile(r, re.UNICODE), fn) for (r, fn) in l]


def main():
    """Main function"""

    # Configure argument parser
    parser = argparse.ArgumentParser(prog='simple-hangout-bot',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-f', '--config-file', metavar='file',
                        default='simple-hangout-bot.conf',
                        help='configuration file to use')

    args = parser.parse_args()

    # Configuration file
    report('Read configuration from {}'.format(args.config_file))
    config = bot.config.Config(args.config_file)
    s = 'Global'

    # Set default configuration
    config.add_option(s, 'name', 'Bot')
    config.add_option(s, 'cookies', 'cookies.json')
    config.add_option(s, 'dbfile', 'default.db')
    config.add_option(s, 'addons', 'responder')

    if config.changed():
        config.write()

    # Run, Bot, Run 
    mybot = SimpleHangoutBot(config)
    mybot.run() 


if __name__ == '__main__':
    main()

