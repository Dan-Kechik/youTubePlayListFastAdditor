import base64
import hashlib
import re
import time
import asyncio
import threading
from queue import Queue
from collections import OrderedDict


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
        self.serverLoop = asyncio.get_event_loop()
        self.serverLoop.create_task(self.start_forever())
        self.socket_thread = threading.Thread(target=self.loopServer, args=(), name=self.arguments['taskName'], daemon=True)
        self.socket_thread.start()

    def push(self, q, value):
        self.queue[q].put(value)

    def push_and_wait(self, q, value):
        self.push(q, value)
        self.push(q, 'wait')
        self.queue[q].join()

    def pop(self, q, defVal=None):
        if not self.queue[q].empty():
            message = self.queue[q].get(timeout=2)
        else:
            message = defVal
        return message

    async def processRequests(self, reader, writer):

        # Wait for request from client.
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Received {message!r} from {addr!r}")

        # Push it to queue and wait for its execution.
        self.push_and_wait('fromClient', data)
        # Read arguments for sending and push forward.

        message = self.pop('toClient')
        if not type(message) is bytes:
            writer.write(message.encode())
        else:
            writer.write(message)
        print(f"Send: {message!r}")
        await writer.drain()

    async def handle_echo(self, reader, writer):
        data = await reader.read(1024)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        sockKey = re.findall(r'Sec-WebSocket-Key: .{24}', message)
        if message.find('GET') > -1 and len(sockKey) > 0:
            sockKey = sockKey[0][19:]
            SK = sockKey + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            hash_object = hashlib.sha1(SK.encode())
            dj = hash_object.digest()
            myKey = base64.b64encode(dj).decode('UTF-8')
            #message = 'HTTP/1.1 200 OK\n' + 'Content-Type: text/html\n' + 'Connection: keep-alive\n' + '\n'
                            # 'Connection: keep-alive\n',  # keep-alive, close
                               # header and body should be separated by additional newline
            message = ("HTTP/1.1 101 Web Socket Handshake\n"+'Access-Control-Allow-Credentials: true\n'+
                       'Access-Control-Allow-Headers: content-type\n' + 'Access-Control-Allow-Headers: authorization\n'+
                       'Access-Control-Allow-Headers: x-websocket-extensions\n' + 'Access-Control-Allow-Headers: x-websocket-version\n'+
                       'Access-Control-Allow-Headers: x-websocket-protocol\n' + 'Access-Control-Allow-Origin: null\n'+
                       "Connection: Upgrade\n"+'Date: Sat, 30 May 2020 18:57:27 GMT\n'
                       "Sec-WebSocket-Accept: "+myKey+"\n"+
                       "Upgrade: websocket\n"+"\n")
            # Sec-WebSocket-Protocol: websocket\n
            print('Switching protocols:\n'+message)
        else:
            message = self.pop('toServer', message)
            #message = 'resp'
            #message = ('HTTP/1.1 200 OK\n'+'Content-Type: text/html\n'+'Content-Length: {}'.format(len(message))+'\nConnection: keep-alive\n'+'\n'+message)
        writer.write(message.encode())
        print(f"Send: {message!r}")

        await writer.drain()

    async def start_forever(self):
        name = self.arguments['taskName']
        self.server = await asyncio.start_server(self.tasks[name], self.address[0], self.address[1])

        addr = self.server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with self.server:
            await self.server.serve_forever()


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