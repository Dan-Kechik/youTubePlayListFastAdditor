import time
import asyncio
import threading
from queue import Queue


class echoServer:

    queue = None
    serverLoop = None
    socket_thread = None
    server = None

    def __init__(self):
        # asyncio.run(main())
        self.queue = Queue()
        self.serverLoop = asyncio.get_event_loop()
        self.serverLoop.create_task(self.start_forever())
        self.serverLoop.call_later(5, self.runCallBack)
        # loop.run_forever()
        self.socket_thread = threading.Thread(target=self.loopServer, args=(), name='socket_inout', daemon=True)
        self.socket_thread.start()
        print('The next code')

    async def handle_echo(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        if not self.queue.empty():
            message=self.queue.get(timeout=2)
        writer.write(message.encode())
        print(f"Send: {message!r}")

        await writer.drain()

        #print("Close the connection")
        #writer.close()

    async def start_forever(self):
        self.server = await asyncio.start_server(self.handle_echo, '127.0.0.1', 8888)

        addr = self.server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with self.server:
            await self.server.serve_forever()
        print('End of main')


    def loopServer(self):
        # Serve requests until Ctrl+C is pressed
        try:
            self.serverLoop.run_forever()  #run_until_complete(self.start_forever())
        except KeyboardInterrupt:
            pass

    def runCallBack(self):
        #loop = asyncio.get_running_loop()
        t = self.serverLoop.time()
        str = f'Loop time is {t}'
        print(str)
        self.queue.put(str) #.encode()
        time.sleep(3)
        print(self.serverLoop.time())
        self.serverLoop.call_later(5, self.runCallBack)

    def stopServer(self):
        # Close the server
        self.server.close()
        print("The socket server has been halted.")
        self.serverLoop.stop()
        while self.serverLoop.is_running():
            time.sleep(0.5)
        self.serverLoop.run_until_complete(self.serverLoop.shutdown_asyncgens())
        self.serverLoop.close()
        print("Server loop has been closed.")

    def stop_all(self):
        self.stopServer()
        self.socket_thread.join()
        print('Thread has been joined.')