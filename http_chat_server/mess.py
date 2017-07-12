#!/usr/bin/env python3
import io
from wsgiref.handlers import format_date_time

import h11
import curio
from curio import socket

SERVER_ADDRESS = ("localhost", 8080)
BUFFER_SIZE = io.DEFAULT_BUFFER_SIZE


def basic_headers():
    return [
        ("Date", format_date_time(None).encode("ascii")),
        ("Server", "WeirdChatClient"),
    ]


class ChatServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def mainloop(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(SERVER_ADDRESS)
        self.sock.listen(5)
        while True:
            client, _ = await self.sock.accept()
            async with ClientConnection(self, client) as client_connection:
                await client_connection.respond()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.sock.close()


class ClientConnection:
    # XXX: It might be best to just re-write this class into a wrapper around
    # h11's server Connection and just respond in ChatServer.main_loop
    # directly.

    def __init__(self, server, sock):
        self.server = server

        self.sock = sock
        self.conn = h11.Connection(our_role=h11.SERVER)

    async def _send(self, event):
        await self.sock.sendall(self.conn.send(event))

    async def _recv_data(self):
        if self.conn.they_are_waiting_for_100_continue:
            go_ahead = \
                h11.InformationalResponse(status_code=100,
                                          headers=basic_headers())
            await self._send(go_ahead)
        try:
            data = await self.sock.recv(BUFFER_SIZE)
        except ConnectionError:
            # They've stopped listening.
            # Not much we can do about it here.
            data = b""
        self.conn.receive_data(data)

    async def _next_event(self):
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                await self._recv_data()
                continue
            if isinstance(event, h11.ConnectionClosed):
                return None
            return event

    async def respond(self):
        while True:
            event = await self._next_event()
            if event is None:
                break
            print(event)
            # TODO: Actually handle events.
            if isinstance(event, h11.EndOfMessage):
                await self._send(h11.Response(status_code=200,
                                              headers=basic_headers()))
                await self._send(h11.EndOfMessage())
                break

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.sock.close()


async def main():
    async with ChatServer() as server:
        await server.mainloop()


if __name__ == "__main__":
    curio.run(main)
