#!/usr/bin/env python3
import random
import string

from wsgiref.handlers import format_date_time


def random_id():
    s = "".join(random.choice(string.ascii_letters) for _ in range(0x16))
    return s.encode("utf-8")


def basic_headers():
    return [
        ("Date", format_date_time(None).encode("ascii")),
        ("Server", "WeirdChatClient"),
        ("Connection", "close"),
    ]
