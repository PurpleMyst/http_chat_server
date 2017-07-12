#!/usr/bin/env python3
import json

import h11
import curio
from curio import socket

from .h11_server_socket import H11ServerSocket, basic_headers

__all__ = ["Server"]


class Server:
    def __init__(self, address, *, family=socket.AF_INET):
        self.address = address
        self.sock = socket.socket(family, socket.SOCK_STREAM)

    ##########################################################################
    # HANDLER EXPLANATION:                                                   #
    # 1. An handler must send the h11.Response event with its desired status #
    #    code and headers. This is so an handler can set Cookies, or return  #
    #    errors in case of malformed requests.                               #
    #                                                                        #
    # 2. It also must handle sending its own h11.Data events, because it     #
    #    makes it easier to call the handler, and gives it extra flexibility #
    #    with chunking excetera.                                             #
    #                                                                        #
    # 3. It also must handle sending its own h11.EndOfMessage events, so it  #
    #    can send trailing headers and end the message when it needs to.     #
    #                                                                        #
    # 4. The name format must be _handle_NAME, where NAME is the HTTP method #
    #    but lowercased.                                                     #
    #                                                                        #
    # 5. The calling format is handler(client_sock, headers, json_data)      #
    ##########################################################################

    async def _handle_get(self, client_sock, headers, json_data):
        assert self or client_sock
        print("GET", headers, json_data)

        await client_sock.send(h11.Response(status_code=200,
                                            headers=basic_headers()))
        await client_sock.send(h11.EndOfMessage())

    async def _handle_post(self, client_sock, headers, json_data):
        assert self or client_sock
        print("POST", headers, json_data)

        await client_sock.send(h11.Response(status_code=200,
                                            headers=basic_headers()))
        await client_sock.send(h11.EndOfMessage())

    async def _handle_head(self, client_sock, headers, json_data):
        assert self or client_sock
        print("HEAD", headers, json_data)

        await client_sock.send(h11.Response(status_code=200,
                                            headers=basic_headers()))
        await client_sock.send(h11.EndOfMessage())

    async def _handle_client(self, client_sock):
        async with client_sock:
            method = None
            headers = []
            json_data = bytearray()

            async for event in client_sock.all_events():
                if isinstance(event, h11.Request):
                    method = event.method
                    headers = event.headers
                elif isinstance(event, h11.Data):
                    json_data += event.data
                elif isinstance(event, h11.EndOfMessage):
                    break
                else:
                    raise ValueError("Unknown event type {event.__class__}!")

            if json_data:
                json_data = json.loads(json_data)
            else:
                json_data = {}

            handler_name = "_handle_" + method.lower().decode("utf-8")
            handler = getattr(self, handler_name, None)

            if handler is not None:
                # We don't pass self because the method is already "bound".
                await handler(client_sock, headers, json_data)
            else:
                await client_sock.send(h11.Response(status_code=405,
                                                    headers=basic_headers()))
                await client_sock.send(h11.EndOfMessage())

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
