import base64
import hashlib
import re
import time
import asyncio
import threading
from queue import Queue
from collections import OrderedDict
import websockets


class echoServer:

    queue = {}
    serverLoop = None
    tasks = OrderedDict()
    socket_thread = None
    arguments = OrderedDict()
    server = None
    address = ('127.0.0.1', 8888)

    def __init__(self):
        # Init queues: command to server; commands to client; requests from client.
        self.queue = {'toServer': Queue(), 'toClient': Queue(), 'fromClient': Queue()}
        self.updateTask(self.handle_echo, 'Echo', getStarted=False)

    def updateTask(self, funHandle, name, getStarted=True):
        self.tasks.update({name: funHandle})
        self.arguments.update({'taskName': name})
        if getStarted:
            self.start()

    def start(self):
        self.stop_all()
        self.start_forever()
        self.socket_thread = threading.Thread(target=self.loopServer, args=(), name=self.arguments['taskName'], daemon=True)
        self.socket_thread.start()

    def push(self, q, value):
        self.queue[q].put(value)

    def push_and_wait(self, q, value):
        self.push(q, value)
        self.queue[q].join()

    def pop(self, q, defVal=None):
        if not self.queue[q].empty():
            message = self.queue[q].get(timeout=2)
        else:
            message = defVal
        return message

    async def processRequests(self, websocket, path):
        while True:
            try:
                # Wait for request from client.
                data = await websocket.recv()
                print(f"Received {data!r} from {path!r}")

                # Push it to queue and wait for its execution.
                self.push_and_wait('fromClient', data)
                print('Awaited backend operations.')

                # Read arguments for sending and push forward.
                message = self.pop('toClient')
                await websocket.send(message)
                print(f'Sended to client: {message}')

            except websockets.ConnectionClosed:
                print(f"Terminated")
                self.start()

    async def handle_echo(self, websocket, path):
        name = await websocket.recv()
        print(f"< {name}")

        greeting = f"Hello {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")

    def start_forever(self):
        name = self.arguments['taskName']

        #myURL = r'ws://' + self.address[0] + f':{self.address[1]}'
        #async with websockets.connect(myURL) as myServ:
        #    self.server = myServ
        #    await self.consume_handler()
        start_server = websockets.serve(self.tasks[name], self.address[0], self.address[1])
        self.serverLoop = asyncio.get_event_loop()
        self.serverLoop.run_until_complete(start_server)
        #await start_server.ws_server()
        #await start_server()
        #asyncio.get_event_loop().run_until_complete(start_server)
        #asyncio.get_event_loop().run_forever()

        #self.server = await asyncio.start_server(self.tasks[name], self.address[0], self.address[1])

        #addr = self.server.sockets[0].getsockname()
        #print(f'Serving on {addr}')

        #async with self.server:
            #await self.server.serve_forever()


    def loopServer(self):
        # Serve requests until Ctrl+C is pressed
        try:
            self.serverLoop.run_forever()
        except KeyboardInterrupt:
            pass

    def stopServer(self):
        # Close the server
        if not self.server is None:
            self.server.close()
            self.server = None
            print("The socket server has been halted.")
        else:
            print('Server has left off.')
        if not self.serverLoop is None:
            self.serverLoop.stop()
            while self.serverLoop.is_running():
                time.sleep(0.5)
            self.serverLoop.run_until_complete(self.serverLoop.shutdown_asyncgens())
            self.serverLoop.close()
            self.serverLoop = None
            print("Server loop has been closed.")
        else:
            print('Server loop has been left off.')

    def stop_all(self):
        self.stopServer()
        if not self.socket_thread is None:
            self.socket_thread.join()
            self.socket_thread = None
            print('Thread has been joined.')
        else:
            print('Thread has been left off.')

    def __del__(self):
        self.stop_all()