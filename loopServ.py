# server made with asyncio
# flake8: noqa


import asyncio
from socket import (socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET)
import time


async def start_server(sock):
    print('Awaining for starting...')
    server = await loop.create_server(asyncio.Protocol, sock=sock)
    print(dir(server))
    print('server started ?')


async def poll(sock):
    print('Starting to poll...')
    conn, addr = await loop.sock_accept(sock)
    await loop.sock_sendall(conn, b'welcome')
    while True:
        data = await loop.sock_recv(conn, 1024)
        print('Got:', data)
    print('Finished poll')


def runCallBack():
    loop = asyncio.get_running_loop()
    print(loop.time())
    time.sleep(3)
    print(loop.time())
    loop.call_later(5, runCallBack)


loop = asyncio.get_event_loop()
loop.set_debug(True)
#Coroutines order
#pipes

sock = socket(AF_INET, SOCK_STREAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sock.bind(('127.0.0.1', 8888))

loop.create_task(poll(sock))
loop.create_task(loop.create_server(asyncio.Protocol, sock=sock))
loop.call_later(5, runCallBack)
loop.run_forever()