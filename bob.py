import random
import socket
import struct

QUBIT_COUNT = 100

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

def receive_sample_data(alice: socket.socket):
    sample_size = alice.recv(4)
    sample_size = struct.unpack('!I', sample_size)[0]
    sample_indices = []
    for _ in range(sample_size):
        alice_bit = alice.recv(4)
        alice_bit = struct.unpack('!I', alice_bit)[0]
        sample_indices.append(alice_bit)
    return sample_size, sample_indices

def receive_sample_from_alice(alice: socket.socket, sample_size):
    alice_sample = []
    for _ in range(sample_size):
        a = alice.recv(4)
        a = struct.unpack('!I', a)[0]
        alice_sample.append(a)
    return alice_sample

def send_sample_to_alice(alice: socket.socket, bob_sample):
    for i in bob_sample:
        alice.send(struct.pack('!I', i))


def get_rem_key(sample_indices, key):
    fin_key = [key[i] for i in sample_indices]
    return fin_key

def error_estimation(sifted_key_alice, sifted_key_bob, sample_size=None):
    errors = 0
    for idx in range(sample_size):
        if sifted_key_alice[idx] != sifted_key_bob[idx]:
            errors += 1

    qber = (errors / sample_size) * 100
    print(f"Sample size: {sample_size} bits")
    print(f"Errors detected: {errors}")
    print(f"QBER: {qber:.2f}%")

    return qber


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

    alice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    alice_socket.connect(('localhost', 4567))

    for qbit in y:
        alice_socket.sendall(struct.pack("!I", qbit ))

    alice_bases = []
    for _ in range(QUBIT_COUNT):
        result = alice_socket.recv(4)
        result = struct.unpack('!I', result)[0]
        alice_bases.append(result)

    print("Alice's bases: ", alice_bases)
    print("Bob's bases: ", y)

    matching_indices, sifted_key_bob = compare_bases(x, y, alice_bases)
    print(f'Bob\'s key:\t{sifted_key_bob}')

    sample_size, sample_indices = receive_sample_data(alice_socket)

    bob_sample = []
    for i in sample_indices:
        bob_sample.append(sifted_key_bob[i])


    alice_sample = receive_sample_from_alice(alice_socket, sample_size)
    send_sample_to_alice(alice_socket, bob_sample)

    print(f'Alice sample:\t{alice_sample}')
    print(f'Bob sample:\t{bob_sample}')

    qber = error_estimation(bob_sample, alice_sample, sample_size)


    key = get_rem_key(sample_indices, sifted_key_bob)
    print(f'Key: {key}')

    alice_socket.close()

if __name__ == "__main__":
    main()
