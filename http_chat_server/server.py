#!/usr/bin/env python3
from curio import socket

from .h11_server_socket import H11ServerSocket

__all__ = ["Server"]


class Server:
    def __init__(self, address, *, family=socket.AF_INET):
        self.address = address
        self.sock = socket.socket(family, socket.SOCK_STREAM)

    async def _exhaust_client(self, sock):
        return b""

    async def mainloop(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.address)
        self.sock.listen(5)
        print("Starting!")
        while True:
            client_sock, _ = await self.sock.accept()
            print("Got connection.")
            client_sock = H11ServerSocket(client_sock)

            async with client_sock:
                async for event in client_sock.all_events():
                    print(event)

            print("Done with connection.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.sock.close()
