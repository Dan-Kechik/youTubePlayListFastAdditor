import socket
import asyncio
import time


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    '''''
    while True:
        string = message + ' - ' + data.decode()
        writer.write(string.encode())
        await writer.drain()
        time.sleep(1)
        print('Iteration')
    '''''

    #print('Close the connection')
    #writer.close()


while True:
    asyncio.run(tcp_echo_client('Hello World!'))
    time.sleep(1)

