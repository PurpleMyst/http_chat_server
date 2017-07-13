#!/usr/bin/env python3
import curio
from curio import socket

from .h11_server_socket import H11ServerSocket
from .client_handler import ClientHandler
from .utils import random_id

__all__ = ["Server"]


class Server:
    def __init__(self, address, *, family=socket.AF_INET):
        self.address = address
        self.sock = socket.socket(family, socket.SOCK_STREAM)

        self.client_ids = {}
        self.missing_messages = {}

    async def _handle_client(self, client_sock):
        async with client_sock:
            client_handler = ClientHandler(self, client_sock)
            await client_handler.fetch_data()
            await client_handler.respond()

    def check_client_id(self, username, cookie):
        # Checks a client's id against their username.
        # Returns a tuple of the format:
        # (success bool, new cookie value)

        if username in self.client_ids:
            # We know the username.
            if self.client_ids[username] == cookie:
                # This client is the owner of the username and thus is
                # authorized.
                return True, cookie
            else:
                # This client is impersonating the username and thus is
                # unauthorized.
                return False, cookie
        else:
            # We don't know the username.
            # This may be a new user, or an old user coming back after a server
            # restart.
            # We should register this username.
            self.client_ids[username] = random_id()
            self.missing_messages[username] = []
            return True, self.client_ids[username]

    async def mainloop(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.address)
        self.sock.listen(5)

        # The task group handles the joining of the sub-coroutines.
        async with curio.TaskGroup() as g:
            while True:
                client_sock, _ = await self.sock.accept()
                client_sock = H11ServerSocket(client_sock)

                await g.spawn(self._handle_client, client_sock)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.sock.close()
