#!/usr/bin/env python3
import h11
from wsgiref.handlers import format_date_time

__all__ = ["H11ServerSocket"]


def basic_headers():
    return [
        ("Date", format_date_time(None).encode("ascii")),
        ("Server", "WeirdChatClient"),
    ]


class H11ServerSocket:
    def __init__(self, sock):
        self.sock = sock
        self.conn = h11.Connection(our_role=h11.SERVER)

    async def _recv_data(self):
        if self.conn.they_are_waiting_for_100_continue:
            go_ahead = \
                h11.InformationalResponse(status_code=100,
                                          headers=basic_headers())
            await self._send(go_ahead)
        try:
            data = await self.sock.recv(4096)
        except ConnectionError:
            # They've stopped listening.
            # Not much we can do about it here.
            data = b""
            return False
        self.conn.receive_data(data)
        return True

    async def send(self, event):
        await self.sock.sendall(self.conn.send(event))

    async def next_event(self):
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                still_listening = await self._recv_data()
                if still_listening:
                    continue
                else:
                    return None
            elif isinstance(event, h11.ConnectionClosed):
                return None
            else:
                return event

    async def all_events(self):
        while True:
            event = await self.next_event()
            if event is None:
                break
            else:
                yield event

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.sock.close()
