import random
import socket
import struct

QUBIT_COUNT = 50

def compare_bases(x_b, y_b, y_a):
    """
    Alice and Bob compare bases over classical channel.
    They keep only the bits where their bases matched.
    """
    print("Step 2: Basis Reconciliation")
    print("-" * 50)
    print("Alice and Bob compare their bases...")

    matching_indices = []
    sifted_key_bob = []

    print(f'Alice\'s bases:\t{y_a}')
    print(f'Bob\'s bases:\t{y_b}')

    for i in range(QUBIT_COUNT):
        if y_a[i] == y_b[i]:  # Bases match
            matching_indices.append(i)
            sifted_key_bob.append(x_b[i])

    print(f"✓ Bases matched for {len(matching_indices)}/{QUBIT_COUNT} qubits")
    print(f"✓ Sifted key length: {len(sifted_key_bob)} bits\n")

    return matching_indices, sifted_key_bob

def main():
    y = [random.randint(0, 1) for _ in range(QUBIT_COUNT)]
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
    for _ in range(QUBIT_COUNT):
        result = client_socket.recv(4)
        result = struct.unpack('!I', result)[0]
        alice_bases.append(result)

    print("Alice's bases: ", alice_bases)
    print("Bob's bases: ", y)

    matching_indices, sifted_key_bob = compare_bases(x, y, alice_bases)
    print(f'Bob\'s key:\t{sifted_key_bob}')

    client_socket.close()
if __name__ == "__main__":
    main()
