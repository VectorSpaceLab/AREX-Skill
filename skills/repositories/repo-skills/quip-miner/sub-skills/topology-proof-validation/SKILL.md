---
name: topology-proof-validation
description: "Use this quip-miner sub-skill for D-Wave topology files, solver
  ranges, topology hash/proof data, winning-solution validation, dumped BQMs,
  and topology troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Topology and Proof Validation

Use this sub-skill when the user needs to inspect QuIP topology files, validate topologies against D-Wave hardware, interpret solver h/J ranges, download/revalidate on-chain wins, dump BQMs, or diagnose topology/proof mismatches.

## Route By Task

- **Topology files and proof artifacts:** Read `references/topology-and-proof-data.md` for `dwave_topologies`, default/production topology targets, winning-solution archive commands, BQM dump shape, and energy/difficulty semantics.
- **D-Wave solver ranges:** Read `references/dwave-solver-ranges.md` for h/J/extended-J/per-qubit coupling ranges and current QPoW headroom.
- **Failures:** Read `references/troubleshooting.md` for missing topology files, invalid subgraphs, topology hash mismatches, solver range overshoot, and live QPU safety.
- **Subgraph check:** Use `scripts/validate_topology_subgraph.py` to compare a candidate topology JSON/GZip file against a reference topology file.

## Common Commands

```bash
python scripts/validate_topology_subgraph.py --reference dwave_topologies/topologies/advantage2_system1.json.gz --candidate path/to/topology.json.gz
python scripts/download_and_validate_wins.py --url wss://qpu-1.nodes.quip.network/rpc --max 50 --dump-bqm --out quip_wins
python scripts/dump_solver_ranges.py --stdout-only
```

The latter two bundled helpers may require network, chain access, or D-Wave credentials. Provide commands; do not run them without approval.

## Key Rules

- `submit_proof` stores a compact seed/proof, not the full BQM. `--dump-bqm` reconstructs Ising models from nonce + topology snapshot.
- Current QPoW emits ternary `h in {-1,0,+1}` and binary `J in {-1,+1}`, inside standard D-Wave ranges.
- `extended_j_range`, per-qubit coupling guards, anneal schedules, reverse anneal, and normalization helpers are headroom/not currently used by QPoW.
- Live miners bind to chain-registered topology; topology validation tools are for analysis, proof replay, and maintaining topology files.
- Do not run QPU benchmarks in the background; live QPU actions require credentials, network, cost, and explicit operator approval.

## Boundaries

- Route live backend commands and QPU budgets to `../mining-backends/SKILL.md`.
- Route attempt archive REST queries to `../telemetry-attempt-archive/SKILL.md`.
- Route source-level tests/release checks to `../maintainer-testing-release/SKILL.md`.
