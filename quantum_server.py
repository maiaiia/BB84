"""
BB84 Quantum Server - Simulates the Quantum Channel
This server receives qubits from Alice and measurements from Bob,
performs quantum operations, and returns results.
"""

import socket, struct
import json
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit import transpile

# Configuration
HOST = 'localhost'
PORT_ALICE = 5001  # Port for Alice's connection
PORT_BOB = 5002  # Port for Bob's connection
N = 50  # Message length (number of qubits)

# Simulator
simulator = AerSimulator()

def transform(x_i, y_i):
    """
    Prepare a qubit based on bit (x_i) and basis (y_i).
    y_i = 0: Z basis, y_i = 1: X basis
    Returns a quantum circuit with the prepared state.
    """
    qr = QuantumRegister(1)
    cr = ClassicalRegister(1)
    qc = QuantumCircuit(qr, cr)

    if y_i == 0:  # Z basis
        if x_i == 0:
            qc.id(0)  # |0⟩ state
        else:
            qc.x(0)  # |1⟩ state
    else:  # X basis
        if x_i == 0:
            qc.h(0)  # |+⟩ state
        else:
            qc.x(0)
            qc.h(0)  # |−⟩ state

    return qc

def measure(qc, y_i):
    """
    Measure the qubit in basis y_i.
    y_i = 0: Z basis, y_i = 1: X basis
    Returns the measurement result (0 or 1).
    """
    if y_i == 1:  # X basis measurement
        qc.h(0)  # Transform to Z basis

    qc.measure(0, 0)

    # Execute circuit
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts(compiled_circuit)

    measured_bit = int(list(counts.keys())[0])
    return measured_bit

def handle_qubit_transmission(qubit_number, x_a, y_a, y_b):
    """
    Process one qubit transmission:
    1. Receive Alice's (x_i, y_i)
    2. Prepare quantum state
    3. Receive Bob's basis
    4. Measure and return result to Bob
    """

    # Alice prepares the qubit
    qc = transform(x_a, y_a)

    # Bob measures in his basis
    measured_bit = measure(qc, y_b)

    return measured_bit

def receive_from_alice(alice_socket: socket.socket):
    x_i = alice_socket.recv(4)
    x_i = struct.unpack('!I', x_i)[0]
    y_i = alice_socket.recv(4)
    y_i = struct.unpack('!I', y_i)[0]
    return x_i, y_i

def receive_from_bob(bob_socket: socket.socket):
    y_i = bob_socket.recv(4)
    y_i = struct.unpack('!I', y_i)[0]
    return y_i

def main():
    print("=" * 60)
    print("BB84 QUANTUM SERVER - Simulating Quantum Channel")
    print("=" * 60)
    print(f"Message length: {N} qubits")
    print(f"Listening for Alice on port {PORT_ALICE}")
    print(f"Listening for Bob on port {PORT_BOB}")
    print("=" * 60)
    print()

    # Create sockets for Alice and Bob
    alice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bob_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow address reuse
    alice_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bob_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind sockets
    alice_socket.bind((HOST, PORT_ALICE))
    bob_socket.bind((HOST, PORT_BOB))

    # Listen for connections
    alice_socket.listen(1)
    bob_socket.listen(1)

    print("Waiting for Alice to connect...")
    alice_conn, alice_addr = alice_socket.accept()
    print(f"✓ Alice connected from {alice_addr}")

    print("Waiting for Bob to connect...")
    bob_conn, bob_addr = bob_socket.accept()
    print(f"✓ Bob connected from {bob_addr}")
    print()

    print("Starting quantum transmission...")
    print("-" * 60)

    # Process N qubits
    for i in range(N):
        # Receive from Alice: (x_i, y_i)
        x_a, y_a = receive_from_alice(alice_conn)

        y_b = receive_from_bob(bob_conn)

        # Process quantum transmission
        measured_bit = handle_qubit_transmission(i, x_a, y_a, y_b)

        # Send result to Bob
        bob_conn.send(struct.pack('!I', measured_bit))

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{N} qubits...")

    print(f"✓ All {N} qubits transmitted successfully!")
    print()

    # Close connections
    print("Closing quantum channel...")
    alice_conn.close()
    bob_conn.close()
    alice_socket.close()
    bob_socket.close()

    print("✓ Quantum server shutdown complete")
    print("=" * 60)


if __name__ == "__main__":
    main()