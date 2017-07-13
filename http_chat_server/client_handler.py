#!/usr/bin/env python3
import json

import h11

from .utils import basic_headers


class ClientHandler:
    AUTHENTICATION_COOKIE = b"X-Chat-Auth"

    def __init__(self, server, client_sock):
        self.server = server
        self.client_sock = client_sock

        self.method = None
        self.cookies = {}
        self.json_data = None

        self.fetched = False


    async def _respond_with_json(self, json_data,
                                 extra_headers=None, status_code=200):
        actual_headers = basic_headers()
        if extra_headers is not None:
            actual_headers += extra_headers

        await self.client_sock.send(
            h11.Response(status_code=status_code, headers=actual_headers)
        )

        bson = json.dumps(json_data).encode("utf-8")
        await self.client_sock.send(h11.Data(data=bson))

        await self.client_sock.send(h11.EndOfMessage())

    async def _authenticate_then_respond(self, json_resp):
        if "username" not in self.json_data:
            await self._respond_with_json({
                "success": False,
                "error": "No username specified.",
            }, status_code=400)
            return

        username = self.json_data["username"]
        cookie = self.cookies.get(self.AUTHENTICATION_COOKIE)

        success, cookie = self.server.check_client_id(username, cookie)

        if success:
            if "success" not in json_resp:
                json_resp["success"] = True

            await self._respond_with_json(json_resp, extra_headers=[
                (b"Set-Cookie", b"%s=%s" % (self.AUTHENTICATION_COOKIE, cookie))
            ])
        else:
            await self._respond_with_json({
                "success": False,
                "error": "Invalid authentication."
            }, status_code=400)

    async def fetch_data(self):
        assert not self.fetched, "fetch_data must be called only once!"

        raw_request_body = bytearray()

        async for event in self.client_sock.all_events():
            if isinstance(event, h11.Request):
                self.method = event.method

                for key, value in event.headers:
                    if key == b"cookie":
                        cookie_key, cookie_value = value.split(b"=", 1)
                        self.cookies[cookie_key] = cookie_value
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
