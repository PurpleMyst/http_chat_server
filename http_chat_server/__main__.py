#!/usr/bin/env python3
import curio

from .server import Server


async def main():
    async with Server(("localhost", 8080)) as server:
        await server.mainloop()


if __name__ == "__main__":
    curio.run(main)
