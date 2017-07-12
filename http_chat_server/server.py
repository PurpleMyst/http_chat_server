#!/usr/bin/env python3
import json

import h11
import curio
from curio import socket

from .h11_server_socket import H11ServerSocket, basic_headers
from .client_handler import ClientHandler

__all__ = ["Server"]


class Server:
    def __init__(self, address, *, family=socket.AF_INET):
        self.address = address
        self.sock = socket.socket(family, socket.SOCK_STREAM)

    async def _handle_client(self, client_sock):
        client_handler = ClientHandler(self, client_sock)
        await client_handler.fetch_data()
        await client_handler.respond()

    async def mainloop(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.address)
        self.sock.listen(5)
        print("Starting!")

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
