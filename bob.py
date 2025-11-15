import random
import socket
import struct

N = 50

def main():
    y = [random.randint(0, 1) for _ in range(N)]
    x = []

    qserver = socket.create_connection(('localhost', 5002))
    for qbit in y:
        qserver.sendall(struct.pack("!I", qbit))
        x_i = qserver.recv(4)
        x_i = struct.unpack("!I", x_i)[0]
        x.append(x_i)


    qserver.close()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 4567))

    for qbit in y:
        client_socket.sendall(struct.pack("!I", qbit ))

    alice_bases = []
    for _ in range(N):
        result = client_socket.recv(4)
        result = struct.unpack('!I', result)[0]
        alice_bases.append(result)

    print("Alice's bases: ", alice_bases)
    print("Bob's bases: ", y)

    client_socket.close()
if __name__ == "__main__":
    main()
