# Fidelity choices and runtime adaptation

## Fidelity semantics

Both fidelity kernels implement

```text
K(x, y) = |<phi(x) | phi(y)>|^2
```

`FidelityStatevectorKernel` prepares `phi(x)` and `phi(y)` as classical
statevector data and computes the overlap directly. It is a reference
implementation for classical simulation. It supports exact overlaps (`shots=None`)
or a binomial shot-noise model (`shots` set) and does not require a sampler.

`FidelityQuantumKernel` delegates paired state preparation to a
`BaseStateFidelity`. The built-in `ComputeUncompute` uses a sampler and forms
`circuit_1.compose(circuit_2.inverse())`, measures all qubits, then extracts the
probability of integer bitstring `0` for global fidelity. It clips public
`fidelities` to `[0, 1]` while retaining `raw_fidelities` in the result. With
`local=True`, it instead averages the probability of zero on each qubit; this
is not interchangeable with the global fidelity for general states.

The fidelity circuit cache is keyed by the circuit pair. Parameter values are
bound at execution time. A single circuit or equal-length lists can be passed
to `ComputeUncompute.run`; list lengths and circuit qubit counts must match.
Input circuits with final measurements are stripped of final measurements before
composition, so users should not treat input measurement instructions as part of
the fidelity state preparation.

## Runtime options and precedence

`ComputeUncompute` merges options in this order (highest priority first):

1. keyword options supplied to `run`;
2. options supplied to `ComputeUncompute(..., options=...)`;
3. sampler defaults.

Use the sampler's supported option names. Kernel `max_circuits_per_job` is a
separate batching control and should not be confused with shots or other
primitive options.

## Pass managers and backend layouts

Some backend/runtime samplers require circuits to be transpiled before submission.
In that case, construct one pass manager for the same target backend and provide
it to `ComputeUncompute`:

```python
from qiskit_machine_learning.state_fidelities import ComputeUncompute

fidelity = ComputeUncompute(
    sampler=backend_compatible_sampler,
    pass_manager=backend_compatible_pass_manager,
)
```

The pass manager runs after the compute-uncompute circuit is built. It must
preserve the circuit's measurements and produce a circuit accepted by the
sampler's target, including its virtual-to-physical qubit layout and classical
register conventions. If the pass manager was generated for a different qubit
count, coupling map, basis gate set, or backend, transpilation or result
post-processing can fail. Treat a pass-manager/sampler/backend triple as one
configuration and validate it with one small fidelity call before a large
kernel matrix.

A particularly subtle implementation detail is layout-aware post-processing:
`ComputeUncompute` checks a transpiled circuit layout for `_input_qubit_count`
and uses that count to distinguish valid virtual-qubit outcomes from additional
physical bits. A custom pass manager or runtime transpiler that changes layout
metadata unexpectedly can therefore produce wrong or empty fidelity values even
if circuit submission succeeds. Inspect the resulting circuit's `layout`,
qubit count, measurement mapping, and a known-state fidelity (identical states
should be near 1) when debugging.

## Runtime adaptation checklist

1. Confirm the sampler is a compatible public `BaseSamplerV2` implementation for
   the installed Qiskit release.
2. Confirm feature-map qubit count, pass-manager target qubit count, and sampler
   backend target agree.
3. Create `ComputeUncompute` with only supported options and, if needed, the
   matching pass manager.
4. Run one identical-circuit pair and one distinct pair; check result length,
   `[0, 1]` bounds, and expected fidelity ordering.
5. Run a two- or three-sample kernel and inspect matrix shape, symmetry, unit
   diagonal policy, and metadata.
6. Only then increase `max_circuits_per_job`, shots, circuit depth, or dataset
   size.

## Version and primitive migration

The migration documentation demonstrates the current V2 pattern with
`StatevectorSampler`/a runtime `SamplerV2`,
`qiskit_machine_learning.state_fidelities.ComputeUncompute`, and
`FidelityQuantumKernel`. When using IBM Runtime or another provider, keep the
provider's documented public imports and use its supported sampler options.
Do not silently substitute an incompatible V1 primitive because a constructor
name looks similar; verify the installed sampler interface and result format.
