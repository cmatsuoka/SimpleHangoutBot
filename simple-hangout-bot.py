#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import appdirs
import argparse
import asyncio
import hangups
import os
import re
import signal
import sys
import time

import bot.config
import bot.addon
from bot.addons import *

class SimpleHangoutBot(object):
    """Bot main class"""
    def __init__(self, config, cookies_path, max_retries=5):
        self._client = None
        self._cookies_path = cookies_path
        self._max_retries = max_retries

        # These are populated by on_connect when it's called.
        self._conv_list = None # hangups.ConversationList
        self._user_list = None # hangups.UserList

        # Our add-ons
        self._addons = bot.addon.addons(config)

        print('Add-ons:')
        for addon in self._addons:
            print('- {0}'.format(addon.name))
        print()

        # List with handled msgs.
        self._res_list = [ ]

        for addon in self._addons:
            self._res_list += self._re_list(addon.get_res_list())

        # Handle signals
        try:
            loop = asyncio.get_event_loop()
            for signum in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(signum, lambda: self.stop())
        except NotImplementedError:
            pass

    def _re_list(self, l):
        """Return a list with functions for compiled regex"""
        return [(re.compile(r, re.UNICODE), fn) for (r, fn) in l]


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

    parser.add_argument('-f', '--config-file', metavar='file',
                        default='simple-hangout-bot.conf',
                        help='configuration file to use')

    args = parser.parse_args()

    config = bot.config.Config(args.config_file)

    # Create necessary directories.
    for path in [args.cookies]:
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                sys.exit('Failed to create directory: {}'.format(e))

    # Run, Bot, Run 
    mybot = SimpleHangoutBot(config, args.cookies)
    mybot.run() 

if __name__ == '__main__':
    print(main())
