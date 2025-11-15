# General
import numpy as np

# Qiskit imports
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit import transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import random
import time

QUBIT_COUNT = 50
# ------------------

# Alice's bits and bases, Bob's bases, Bob's received bits
x_a = []  # Alice's bits (0 or 1)
y_a = []  # Alice's bases (0=Z, 1=X)
x_b = []  # Bob's measured bits
y_b = []  # Bob's bases (0=Z, 1=X)

# -------- CHANNELS ---------
quantumChannel = -1
classicalChannel = -1

# -------- REGISTERS -------
quantumRegister = -1
classicalRegister = -1

# Simulator
simulator = AerSimulator()


def transform(x_i, y_i):
    """
    Alice prepares a qubit based on her bit (x_i) and basis (y_i).
    y_i = 0: Z basis (computational basis)
    y_i = 1: X basis (Hadamard basis)

    Returns a quantum circuit with the prepared state.
    """
    qr = QuantumRegister(1)
    cr = ClassicalRegister(1)
    qc = QuantumCircuit(qr, cr)

    if y_i == 0:  # Z basis
        if x_i == 0:
            # |0⟩ state - already initialized
            qc.id(0)
        else:  # x_i == 1
            # |1⟩ state - flip the qubit
            qc.x(0)
    else:  # y_i == 1, X basis
        if x_i == 0:
            # |+⟩ state = (|0⟩ + |1⟩)/√2
            qc.h(0)
        else:  # x_i == 1
            # |−⟩ state = (|0⟩ - |1⟩)/√2
            qc.x(0)
            qc.h(0)

    return qc


def translate(qc, y_i):
    """
    Bob measures the qubit in his chosen basis (y_i).
    y_i = 0: Z basis (computational basis)
    y_i = 1: X basis (Hadamard basis)

    Returns the measurement result.
    """
    # if y_i == 0, no transformations needed

    if y_i == 1:  # X basis measurement
        # Transform from X basis to Z basis before measuring
        qc.h(0)

    # Measure in Z basis
    qc.measure(0, 0)

    # Execute the circuit
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts(compiled_circuit)

    # Extract the measurement result
    measured_bit = int(list(counts.keys())[0])

    return measured_bit


def set_up():
    """Initialize all random values and data structures."""
    global x_a, y_a, y_b, x_b, quantumRegister, classicalRegister

    # Generate Alice's random bits and bases
    x_a = [random.randint(0, 1) for _ in range(QUBIT_COUNT)]
    y_a = [random.randint(0, 1) for _ in range(QUBIT_COUNT)]

    # Generate Bob's random bases
    y_b = [random.randint(0, 1) for _ in range(QUBIT_COUNT)]

    # Bob's received bits (to be filled)
    x_b = []

    print("=" * 50)
    print("BB84 Quantum Key Distribution Protocol")
    print("=" * 50)
    print(f"Number of qubits: {QUBIT_COUNT}\n")


def send_qubit(qbit_number):
    """
    Alice prepares and sends a single qubit.
    Bob receives and measures it.
    """
    # Alice prepares the qubit
    x_i = x_a[qbit_number]  # Alice's bit
    y_i = y_a[qbit_number]  # Alice's basis

    # Create the quantum circuit with Alice's prepared state
    qc = transform(x_i, y_i)

    # Bob measures in his chosen basis
    y_bob = y_b[qbit_number]
    measured_bit = translate(qc, y_bob)

    return measured_bit


def send_full_message():
    """Alice sends all qubits to Bob."""
    global x_b

    print("Step 1: Quantum Transmission")
    print("-" * 50)
    print("Alice is sending qubits to Bob...")

    for i in range(QUBIT_COUNT):
        measured_bit = send_qubit(i)
        x_b.append(measured_bit)

    print(f"✓ All {QUBIT_COUNT} qubits transmitted and measured\n")


def compare_bases():
    """
    Alice and Bob compare bases over classical channel.
    They keep only the bits where their bases matched.
    """
    print("Step 2: Basis Reconciliation")
    print("-" * 50)
    print("Alice and Bob compare their bases...")

    matching_indices = []
    sifted_key_alice = []
    sifted_key_bob = []

    print(f'Alice\'s bases:\t{y_a}')
    print(f'Bob\'s bases:\t{y_b}')

    for i in range(QUBIT_COUNT):
        if y_a[i] == y_b[i]:  # Bases match
            matching_indices.append(i)
            sifted_key_alice.append(x_a[i])
            sifted_key_bob.append(x_b[i])

    print(f"✓ Bases matched for {len(matching_indices)}/{QUBIT_COUNT} qubits")
    print(f"✓ Sifted key length: {len(sifted_key_alice)} bits\n")

    return matching_indices, sifted_key_alice, sifted_key_bob


def error_estimation(sifted_key_alice, sifted_key_bob, sample_size=None):
    """
    Estimate the quantum bit error rate (QBER) by comparing a sample.
    """
    if sample_size is None: # select a sample size of around 25% of the bits (but send at most 20 bits)
        sample_size = min(len(sifted_key_alice) // 4, 20)

    print("Step 3: Error Estimation")
    print("-" * 50)

    if len(sifted_key_alice) < sample_size:
        print("⚠ Not enough bits for error estimation")
        return sifted_key_alice, sifted_key_bob, 0

    # Random sample for error checking
    sample_indices = random.sample(range(len(sifted_key_alice)), sample_size)
    # in theory, these should also be sent via the regular channel

    errors = 0
    for idx in sample_indices:
        if sifted_key_alice[idx] != sifted_key_bob[idx]:
            errors += 1

    qber = (errors / sample_size) * 100
    print(f"Sample size: {sample_size} bits")
    print(f"Errors detected: {errors}")
    print(f"QBER: {qber:.2f}%")

    # Remove sampled bits from the key
    remaining_alice = [sifted_key_alice[i] for i in range(len(sifted_key_alice))
                       if i not in sample_indices]
    remaining_bob = [sifted_key_bob[i] for i in range(len(sifted_key_bob))
                     if i not in sample_indices]

    print(f"✓ Final key length: {len(remaining_alice)} bits\n")

    return remaining_alice, remaining_bob, qber


def display_summary(final_key_alice, final_key_bob, qber):
    """Display a summary of the BB84 protocol execution."""
    print("=" * 50)
    print("PROTOCOL SUMMARY")
    print("=" * 50)
    print(f"Initial qubits sent:     {QUBIT_COUNT}")
    print(f"Final shared key length: {len(final_key_alice)} bits")
    print(f"Efficiency:              {(len(final_key_alice) / QUBIT_COUNT) * 100:.1f}%")
    print(f"QBER:                    {qber:.2f}%")
    print(f"\nAlice's key (first 20): {final_key_alice[:20]}")
    print(f"Bob's key (first 20):   {final_key_bob[:20]}")
    print("=" * 50)


def main():
    """Main BB84 protocol execution."""
    random.seed(time.time())

    # Setup
    set_up()

    # Step 1: Quantum transmission
    send_full_message()

    # Step 2: Basis reconciliation
    matching_indices, sifted_key_alice, sifted_key_bob = compare_bases()

    # Step 3: Error estimation
    final_key_alice, final_key_bob, qber = error_estimation(
        sifted_key_alice, sifted_key_bob
    )

    # Summary
    display_summary(final_key_alice, final_key_bob, qber)


if __name__ == "__main__":
    main()


# TODO - eve
# TODO - separate
# TODO - if error is too big, announce that the key is corrupted