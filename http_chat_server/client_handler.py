#!/usr/bin/env python3
import json

import h11

from .h11_server_socket import basic_headers


class ClientHandler:
    def __init__(self, server, client_sock):
        self.server = server
        self.client_sock = client_sock

        self.method = None
        self.headers = []
        self.json_data = None

        self.fetched = False

    async def _respond_with_json(self, json_data, extra_headers=None):
        actual_headers = basic_headers()
        if extra_headers is not None:
            actual_headers += extra_headers

        await self.client_sock.send(
            h11.Response(status_code=200, headers=actual_headers)
        )

        bson = json.dumps(json_data).encode("utf-8")
        await self.client_sock.send(h11.Data(data=bson))

        await self.client_sock.send(h11.EndOfMessage())

    async def fetch_data(self):
        assert not self.fetched, "fetch_data must be called only once!"

        raw_request_body = bytearray()

        async for event in self.client_sock.all_events():
            if isinstance(event, h11.Request):
                self.method = event.method
                self.headers = event.headers
            elif isinstance(event, h11.Data):
                raw_request_body += event.data
            elif isinstance(event, h11.EndOfMessage):
                break

        if raw_request_body:
            self.json_data = json.loads(raw_request_body)
        else:
            self.json_data = {}

        self.fetched = True

    async def respond(self):
        assert self.fetched, "The data was not fetched!"

        handler_name = "_handle_" + self.method.lower().decode("utf-8")
        handler = getattr(self, handler_name, None)

        if handler is not None:
            await handler()
        else:
            await self.client_sock.send(h11.Response(status_code=405,
                                                     headers=basic_headers()))
            await self.client_sock.send(h11.EndOfMessage())
