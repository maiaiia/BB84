import random
import socket
import struct

N = 50 # number of bits

def main():
    x= [random.randint(0, 1) for _ in range(N)]
    y= [random.randint(0, 1) for _ in range(N)]

    qserver = socket.create_connection(('localhost', 5001))
    for (bit, qbit) in zip(x, y):
         qserver.sendall(struct.pack("!I",bit ))
         qserver.sendall(struct.pack("!I",qbit ))

    qserver.close()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind(('localhost', 4567))
    client_socket.listen()

    conn, address = client_socket.accept()

    bob_bases = []
    for _ in range(N):
        result = conn.recv(4)
        result = struct.unpack('!I', result)[0]
        bob_bases.append(result)

    for qbit in y:
        conn.sendall(struct.pack("!I", qbit ))

    print("Alice's bases:\t", y)
    print("Bob's bases:\t", bob_bases)

    conn.close()
    client_socket.close()

if __name__ == "__main__":
    main()