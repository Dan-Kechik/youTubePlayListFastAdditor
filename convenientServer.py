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
    events = OrderedDict()
    address = None

    def __init__(self, myHost='127.0.0.1', myPort=8888):
        self.address = (myHost, myPort)
        # Init queues: command to server; commands to client; requests from client.
        self.queue = {'toServer': Queue(), 'toClient': Queue(), 'fromClient': Queue()}
        self.events = {'received': threading.Event(), 'gotAnswer': threading.Event(), 'sendToClient': threading.Event(), 'Terminated': threading.Event()}
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
                e = self.events['received']
                e.set()

                # Push it to queue and wait for its execution.
                self.push_and_wait('fromClient', data)
                print('Awaited backend operations.')
                e = self.events['gotAnswer']
                e.set()

                # Read arguments for sending and push forward.
                message = self.pop('toClient')
                await websocket.send(message)
                print(f'Sended to client: {message}')
                e = self.events['sendToClient']
                e.set()

            except websockets.ConnectionClosed:
                print(f"Terminated")
                e = self.events['Terminated']
                e.set()
                self.stop_all()

    async def handle_echo(self, websocket, path):
        name = await websocket.recv()
        print(f"< {name}")
        e = self.events['received']
        e.set()

        greeting = f"Hello {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")
        e = self.events['sendToClient']
        e.set()

    def start_forever(self):
        name = self.arguments['taskName']
        start_server = websockets.serve(self.tasks[name], self.address[0], self.address[1])
        self.serverLoop = asyncio.get_event_loop()
        self.serverLoop.run_until_complete(start_server)


    def loopServer(self):
        # Serve requests until Ctrl+C is pressed
        try:
            self.serverLoop.run_forever()
        except KeyboardInterrupt:
            pass

    def stopServer(self):
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