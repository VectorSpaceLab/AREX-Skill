# Algorithm recipes

This reference distills Cirq's maintained textbook-algorithm patterns into small reusable recipes. It intentionally avoids copying long examples; use it to assemble a minimal circuit, validation check, and route to sibling sub-skills when lower-level details are needed.

## Common scaffold

For algorithm circuits, keep these invariants explicit:

- Name registers by role: input, output/ancilla, phase/counting, message, sender, receiver, cost/mixer.
- Put terminal measurements at the end unless the algorithm needs mid-circuit measurement and classical control, as in teleportation or superdense-coding demonstrations.
- Choose one validation mode before scaling: exact state-vector/unitary check for small circuits, sampled histogram check for measurement algorithms, or observable expectation check for variational loops.
- Fix random seeds or use deterministic secrets for regression tests; randomized demos are not stable acceptance tests.
- Preserve measurement keys and measurement-qubit order in any histogram interpretation.

Minimal shape:

```python
import cirq
import numpy as np

qubits = cirq.LineQubit.range(n)
circuit = cirq.Circuit()
# prepare -> oracle/unitary/ansatz -> inverse/decoder -> measure/observe
print(circuit.to_text_diagram())
```

For simulator APIs, sweeps, density-matrix runs, noise, and plotting setup, route to `simulation-study-and-noise`. For decomposition, adjacency constraints, and target gatesets, route to `transformers-and-compilation`.

## Quantum Fourier transform (QFT)

Use this when the user needs the frequency-basis transform itself or as a subroutine for phase estimation/order finding.

Preferred Cirq API:

```python
qubits = cirq.LineQubit.range(4)
qft_op = cirq.qft(*qubits, without_reverse=False)
iqft_op = cirq.qft(*qubits, inverse=True, without_reverse=False)
circuit = cirq.Circuit(qft_op)
```

Recipe notes:

- `cirq.qft(*qubits, without_reverse=False, inverse=False)` returns an operation on the given qubits.
- `cirq.QuantumFourierTransformGate(num_qubits, without_reverse=False).on(*qubits)` is the gate-level form.
- `without_reverse=True` omits final swaps. This is often cheaper, but it changes the register order expected by later operations. Document and test the order rather than guessing.
- For manual or adjacency-aware QFT, use Hadamards plus controlled phase rotations, then route layout and swap minimization to `transformers-and-compilation`.

Validation checks:

- For 0 to 5 qubits, compare `cirq.unitary(cirq.Circuit(manual_ops))` against the built-in QFT circuit if you wrote a manual construction.
- On `|00...0>`, QFT produces a uniform-amplitude state. Check amplitudes rather than relying on a measurement histogram alone.
- For inverse QFT, check that QFT followed by inverse QFT is identity up to numerical tolerance for a small register.

## Phase estimation

Use this when the task is to estimate an eigenphase of a unitary `U`.

Circuit pattern:

1. Prepare a target eigenstate of `U` on the target register.
2. Prepare `n` counting qubits with `H.on_each`.
3. Apply controlled powers `U ** (2**i)` from counting qubit `i` to the target.
4. Apply inverse QFT on the counting register.
5. Measure the counting register with a dedicated key such as `"phase"`.

Skeleton:

```python
counting = cirq.LineQubit.range(n_bits)
target = cirq.NamedQubit("target")
U = cirq.Z ** (2 * theta)  # example: eigenphase theta on |1>

circuit = cirq.Circuit(
    cirq.X(target),
    cirq.H.on_each(*counting),
    [U.on(target).controlled_by(counting[i]) ** (2**i) for i in range(n_bits)],
    cirq.qft(*counting, inverse=True, without_reverse=True),
    cirq.measure(*counting, key="phase"),
)
```

Validation checks:

- Use known phases such as `0`, `1/4`, `1/2`, or `3/4` before arbitrary angles.
- Convert the modal measurement integer to `mode / 2**n_bits` only after confirming the measurement key and qubit ordering.
- If using `without_reverse=True`, align the measurement/qubit interpretation with the omitted final swaps.
- If the prepared target is not an exact eigenstate, expect a distribution over eigenphases; do not require a single deterministic bitstring.

## Grover search

Use this when the task is a marked-item/oracle demonstration.

Circuit pattern:

1. Allocate input qubits and one output/phase-kickback ancilla.
2. Initialize the ancilla to `|->` using `X` then `H`; place input qubits in uniform superposition with `H.on_each`.
3. Query an oracle that flips the output/phase for the marked input.
4. Apply the diffuser/inversion-about-mean on input qubits.
5. Measure only the search/input register.

For a 2-bit demo, one Grover iteration is enough. For larger registers, choose the iteration count from the search-space size and number of marked states, then validate on a small fixed secret before scaling.

Validation checks:

- Use deterministic marked bits in tests. Random secrets are acceptable only for demos that print the secret.
- Convert sampled arrays to bitstrings with an explicit `fold_func` that matches the measurement order.
- The most-common result should match the marked bitstring with high probability for the chosen repetitions; do not require every sample to match unless the algorithm setting is deterministic.

## Bernstein-Vazirani

Use this when the task is to recover a hidden bitstring from a linear Boolean oracle.

Circuit pattern:

1. Allocate `n` input qubits and one output qubit.
2. Initialize the output qubit to `|->` using `X` then `H`.
3. Put input qubits into `|+>` with Hadamards.
4. Implement the hidden string by applying `CNOT(input_i, output)` for each factor bit equal to `1`; apply an optional output `X` for the bias.
5. Apply `H` to input qubits and measure the input register.

Validation checks:

- The measured input bitstring should equal the hidden factor bits; the bias bit does not appear in the final measured factor string.
- Keep the input-qubit order used by the oracle and the measurement order identical.

## Quantum teleportation

Use this when the task is to transmit a one-qubit state using an entangled pair plus two classical bits.

Circuit pattern:

1. Allocate message, Alice, and Bob qubits.
2. Build a Bell pair between Alice and Bob using `H(Alice)` then `CNOT(Alice, Bob)`.
3. Prepare the message state on the message qubit.
4. Apply Bell-measurement operations: `CNOT(message, Alice)` and `H(message)`.
5. Measure message and Alice with separate keys.
6. Apply Bob corrections with classical controls: `X(Bob).with_classical_controls(alice_key)` and `Z(Bob).with_classical_controls(message_key)`.

Validation checks:

- Mid-circuit measurements and classical controls are expected here. Do not convert the whole circuit to a unitary.
- For a state-vector simulator validation, compare Bob's final Bloch vector or Pauli expectations against the separately prepared message state.
- Keep correction keys exact; a typo in a classical-control key silently changes the algorithm's meaning.

## Superdense coding

Use this when the task is to encode two classical bits into one transmitted qubit using a shared Bell pair.

Circuit pattern:

1. Prepare or choose two classical bits.
2. Prepare a Bell pair shared by sender and receiver.
3. Encode the bits on the sender's qubit with the standard `X`/`Z` actions.
4. Send/swap the sender qubit to the receiver register if the circuit models movement explicitly.
5. Decode with `CNOT` then `H` and measure the receiver qubits.

Validation checks:

- Use separate keys for input and output records; compare arrays for equality in the specified qubit order.
- If the input bits are generated by measurement inside the same circuit, non-terminal measurement is part of the demonstration, not a circuit-construction error.

## QAOA-like Max-Cut or cost/mixer ansatzes

Use this when the task is a variational circuit with alternating cost and mixer layers.

Circuit pattern:

1. Choose a small graph or cost Hamiltonian first.
2. Prepare uniform superposition with `H.on_each(*qubits)`.
3. For each layer, apply cost unitaries on problem terms, then mixer rotations.
4. Measure all problem qubits with one key.
5. Convert bitstrings to classical objective values and optimize parameters outside the circuit.

Common Cirq ingredients:

```python
def rzz(rads):
    return cirq.ZZPowGate(exponent=2 * rads / np.pi, global_shift=-0.5)

for beta, gamma in zip(betas, gammas):
    circuit.append(rzz(-0.5 * gamma).on(qubits[i], qubits[j]) for i, j in edges)
    circuit.append(cirq.rx(2 * beta).on_each(*qubits))
```

Validation checks:

- Run one fixed parameter set before adding an optimizer.
- Assert output array shape and measurement key presence before computing the objective.
- For parameter sweeps, keep symbol names, resolver keys, and objective arguments aligned; route sampler/sweep details to `simulation-study-and-noise`.
- Optimizer loops with random graphs or stochastic sampling are not stable smoke tests unless seeds, repetitions, and stopping rules are fixed.

## Large textbook examples

Shor/order-finding, HHL, and large stabilizer-code demonstrations are useful educational references but are usually too large for fast acceptance tests when simulated classically. When a user asks for them:

- Start with the smallest meaningful input and a classical consistency check.
- Use known arithmetic corner cases before invoking simulated quantum subroutines.
- Treat long quantum order-finding or linear-system simulation as optional integration evidence, not a routine smoke check.
- If hardware topology or provider execution becomes part of the task, route compilation/provider concerns to sibling sub-skills.
