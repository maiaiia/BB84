import random
import socket
import struct

QUBIT_COUNT = 50 # number of bits

def compare_bases(x_a, y_a, y_b):
    """
    Alice and Bob compare bases over classical channel.
    They keep only the bits where their bases matched.
    """
    print("Step 2: Basis Reconciliation")
    print("-" * 50)
    print("Alice and Bob compare their bases...")

    matching_indices = []
    sifted_key_alice = []

    print(f'Alice\'s bases:\t{y_a}')
    print(f'Bob\'s bases:\t{y_b}')

    for i in range(QUBIT_COUNT):
        if y_a[i] == y_b[i]:  # Bases match
            matching_indices.append(i)
            sifted_key_alice.append(x_a[i])

    print(f"✓ Bases matched for {len(matching_indices)}/{QUBIT_COUNT} qubits")
    print(f"✓ Sifted key length: {len(sifted_key_alice)} bits\n")

    return matching_indices, sifted_key_alice

def request_bit_sample(sifted_key, bob_socket: socket.socket):
    sample_size = min(len(sifted_key) // 4, 20)
    sample_indices = random.sample(range(len(sifted_key)), sample_size)

    bob_socket.send(struct.pack('!I', sample_size))
    for i in sample_indices:
        bob_socket.send(struct.pack('!I', i))

    return sample_size, sample_indices

def send_sample_to_bob(bob: socket.socket, sample):
    for i in sample:
        bob.send(struct.pack('!I', i))

def receive_bob_sample(bob_socket: socket.socket, sample_size):
    bob_sample = []
    for _ in range(sample_size):
        b = bob_socket.recv(4)
        b = struct.unpack('!I', b)[0]
        bob_sample.append(b)
    return bob_sample

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

def get_rem_key(sample_indices, key):
    fin_key = [key[i] for i in sample_indices]
    return fin_key


def estimate_error(alice_sample, bob_sample, sample_size):
    errors = 0
    for i in range(sample_size):
        if alice_sample[i] != bob_sample[i]:
            errors += 1
    qber = (errors / sample_size) * 100

    print(f"Sample size: {sample_size} bits")
    print(f"Errors detected: {errors}")
    print(f"QBER: {qber:.2f}%")

    return qber

def main():
    x= [random.randint(0, 1) for _ in range(QUBIT_COUNT)]
    y= [random.randint(0, 1) for _ in range(QUBIT_COUNT)]

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
    for _ in range(QUBIT_COUNT):
        result = conn.recv(4)
        result = struct.unpack('!I', result)[0]
        bob_bases.append(result)

    for qbit in y:
        conn.sendall(struct.pack("!I", qbit ))

    print("Alice's bases:\t", y)
    print("Bob's bases:\t", bob_bases)

    matching, sifted_key_alice = compare_bases(x, y, bob_bases)
    print(f'Alice\'s key:\t{sifted_key_alice}')

    sample_size, sample_indices = request_bit_sample(sifted_key_alice, conn)
    alice_sample = []
    for i in sample_indices:
        alice_sample.append(sifted_key_alice[i])

    send_sample_to_bob(conn, alice_sample)
    bobs_sample = receive_bob_sample(conn, sample_size)

    print(f'Alice sample:\t{alice_sample}')
    print(f'Bob sample:\t{bobs_sample}')

    qber = estimate_error(alice_sample, bobs_sample, sample_size)

    key = get_rem_key(sample_indices, sifted_key_alice)
    print(key)



    conn.close()
    client_socket.close()

if __name__ == "__main__":
    main()