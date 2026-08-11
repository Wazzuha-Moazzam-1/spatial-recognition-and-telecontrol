import socket 

host = "127.0.0.1"
port = 5005

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((host,port))
 # type: 

def receive_packet():
    while True:
        data, addr = server.recvfrom(1024)
        command = data.decode('utf-8')
        print(command)

if __name__ =="__main__":

    receive_packet()
