import time
from socket import (socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET)
from convenientServer import echoServer

if __name__ == "__main__":
    myServ = echoServer()
    print('Linear code line has been executed.')
    time.sleep(7)
    print('One more line of linear code has been executed.')
    time.sleep(15)
    print('The last line of linear code has been executed.')
    time.sleep(15)
    print('Trying to stop...')
    myServ.stop_all()
    print('Finishing...')

def test1():
    LOCALHOST = "localhost"
    PORT = 9090
    server = socket(AF_INET, SOCK_STREAM)
    server.bind((LOCALHOST, PORT))
    server.listen(1)
    print("Server started")
    print("Waiting for client request..")
    clientConnection, clientAddress = server.accept()
    print("Connected clinet :", clientAddress)
    msg = ''
    while True:
        in_data = clientConnection.recv(1024)
        msg = in_data.decode()
        if msg == 'bye':
            break
        print("From Client :", msg)
        out_data = 'Славянский шкаф'
        http_responce = ('HTTP/1.1 200 OK\n',
                         'Content-Type: text/html\n',
                         'Content-Length: {}'.format(len(out_data)),
                         'Connection: keep-alive\n',  # keep-alive, close
                         '\n',  # header and body should be separated by additional newline
                         out_data)
        str = ''
        for s in http_responce: str = str + s
        #clientConnection.send(bytes(str, 'UTF-8'))
    print("Client disconnected....")
    clientConnection.close()