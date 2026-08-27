# D-Wave Solver Ranges and QPoW Headroom

Solver ranges describe what D-Wave hardware accepts for linear biases (`h`) and couplers (`J`). Recorded examples in the source docs include:

| Solver/chip | Topology | Active/total qubits | `h_range` | `j_range` | `extended_j_range` | Regions |
| --- | --- | --- | --- | --- | --- | --- |
| `Advantage_system4` | Pegasus P16 | about 5627/5760 | `[-4, 4]` | `[-1, 1]` | `[-2, 1]` | `na-west-1` |
| `Advantage_system6` | Pegasus P16 | about 5612/5760 | `[-4, 4]` | `[-1, 1]` | `[-2, 1]` | `na-west-1` |
| `Advantage2_system1` | Zephyr Z(12,4) | about 4577/4800 | `[-6, 6]` | `[-1, 1]` | `[-2, 1]` | `na-west-1` |
| `Advantage2_system4` | Zephyr Z(6,4) | about 1203/1248 | `[-6, 6]` | `[-1, 1]` | `[-2, 1]` | `na-east-1` |

Regenerate current values with the bundled helper:

```bash
python scripts/dump_solver_ranges.py --stdout-only
```

This requires D-Wave API access and should not be run without credentials/approval.

## Field Meanings

- `h_range`: allowed per-qubit linear bias.
- `j_range`: allowed standard-mode coupler value.
- `extended_j_range`: wider negative coupling range when extended-J mode is enabled.
- `per_qubit_coupling_range`: cumulative bound on the sum of coupler magnitudes touching a qubit.
- Active/total qubits: active working qubits vary by solver revision/calibration.

## Current QPoW Usage

The current proof generator emits:

- `h` in `{-1, 0, +1}`.
- `J` in `{-1, +1}`.

These fit inside standard `h_range` and `j_range` for the recorded solvers. No scaling is needed for the current PoW.

## Not Currently Used

Current QPoW does not use:

- `extended_j_range` mode.
- Per-qubit coupling-sum validation.
- Anneal-schedule tuning, reverse anneal, or h-gain schedules.
- Normalization helpers referenced by older docs.

If a future PoW variant pushes beyond ±1 couplers or denser graphs, implement extended-J and per-qubit coupling checks before sending problems to a live QPU.
