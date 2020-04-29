import socket

LOCALHOST = "localhost"
PORT = 15555
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    clientConnection.send(bytes(str, 'UTF-8'))
print("Client disconnected....")
clientConnection.close()