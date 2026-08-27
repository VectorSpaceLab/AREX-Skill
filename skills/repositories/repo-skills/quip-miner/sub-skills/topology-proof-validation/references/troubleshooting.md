# Topology and Proof Troubleshooting

## Topology file not found

Check whether the tool expects a package topology name, a file path, or a file under `dwave_topologies/topologies/`. For bundled validation, pass explicit files with `--reference` and `--candidate` to avoid source-checkout assumptions.

## Invalid subgraph

If candidate nodes or edges are not present in the reference topology, the candidate cannot be directly embedded as that hardware subgraph. Inspect the first missing nodes/edges and confirm node numbering/edge normalization.

## Topology hash mismatch

Live PoW proofs must use the chain-registered topology hash. A local synthetic topology or stale hardware file can produce a proof the chain rejects as invalid topology. Live miners should pull topology from the chain; do not override with `--topology`.

## No registered topology on dev chain

Use `quip-miner bootstrap --seed-chain` only on dev/local chains. Production chains should be seeded/governed out of band.

## Solver range overshoot

Current QPoW uses only ±1 J and -1/0/+1 h. If a custom experiment emits larger values, compare against solver `h_range`, `j_range`, extended-J availability, and per-qubit coupling limits before live sampling.

## Downloaded win fails validation

Capture:

- block number and hash,
- topology hash,
- decoded proof nonce,
- recomputed best energy vs stored energy,
- `num_valid` and diversity,
- runtime/spec version.

A mismatch can indicate chain/runtime drift, wrong topology snapshot, decode changes, or a bad assumption in the validation tool.

## QPU benchmark safety

Do not run QPU benchmarks or canaries in the background. Provide commands and require operator execution because they can consume paid QPU access and credentials.
