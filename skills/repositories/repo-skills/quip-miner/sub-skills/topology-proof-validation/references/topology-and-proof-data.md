# Topology and Proof Data

## Topology Assets

`dwave_topologies/` contains hardware topology files and loader utilities. Typical topology files are GZip JSON under `dwave_topologies/topologies/`, including Advantage2, Pegasus, Chimera, and Zephyr-derived assets.

Important operator targets:

| Topology | Role |
| --- | --- |
| Zephyr Z(9,2) | Default production-size synthetic target documented for QPoW difficulty around -4100. |
| Advantage2_system1 | Full hardware topology / reference solver; around 4577 active qubits in recorded range docs. |
| Advantage2_system4 | Smaller Advantage2 generation variants where available. |

When D-Wave recalibrates, update topology JSON files, verify embeddings/topology compatibility, and delete stale/incompatible assets.

## Difficulty and Energy Semantics

Genesis/dev defaults are relaxed (`difficulty_energy = -2500.0`, `min_diversity = 0.2`, `min_solutions = 5`). Production Z(9,2) targets are around `difficulty_energy = -4100.0`, `min_diversity = 0.15`, `min_solutions = 5`.

The runtime stores energies in milli precision. Tests and proof validation allow only tiny float-rounding slack.

## Winning-solution Validation

The bundled helper `scripts/download_and_validate_wins.py` walks the proof chain backward from `QuantumPow.LastProofBlock`, decodes submitted proofs, fetches mining snapshots, regenerates the Ising model from nonce + topology, recomputes energies/diversity, and writes:

- `<out>.wins.jsonl` — downloaded wins, including packed solution hex.
- `<out>.validation.jsonl` — one independent verdict per win.
- `<out>.bqms.jsonl` when `--dump-bqm` is set.

Example:

```bash
python scripts/download_and_validate_wins.py \
  --url wss://qpu-1.nodes.quip.network/rpc \
  --max 50 \
  --dump-bqm \
  --out quip_wins
```

This is a network/chain operation. Do not run it unless the user asks.

## Dumped BQM Shape

Each BQM JSONL record contains:

- `block_number`
- `nonce`
- `topology_hash`
- `h`: list of `[node_id, bias]`
- `j`: list of `[u, v, coupling]`

Reload into dictionaries:

```python
h = {n: b for n, b in rec["h"]}
J = {(u, v): c for u, v, c in rec["j"]}
```

The BQM is re-derived from nonce + topology snapshot using the same generation function the miner and validator use.

## Topology Subgraph Validation

Use the bundled script when a user has a candidate topology JSON/GZip file and a reference hardware topology file:

```bash
python scripts/validate_topology_subgraph.py --reference advantage2_system1.json.gz --candidate candidate.json.gz --json
```

All candidate nodes and normalized edges must exist in the reference. This validates graph compatibility, not solver calibration/current availability.
