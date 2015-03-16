# -*- coding: utf-8 -*-

from datetime import datetime

def report(msg):
    timestamp = datetime.strftime(datetime.now(), '%H:%M:%S')
    print('\033[1;37m[{}]\033[0m {}'.format(timestamp, msg))

