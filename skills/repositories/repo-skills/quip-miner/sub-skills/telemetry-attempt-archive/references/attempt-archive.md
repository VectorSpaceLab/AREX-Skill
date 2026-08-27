# Mining Attempt Archive

The archive records per-solution mining attempts and selected stored/submitted solutions.

## Directory Precedence

Archive root is resolved in this order:

1. `QUIP_MINING_ATTEMPTS_DIR`.
2. `$QUIP_RUNTIME_DIR/mining_attempts`.
3. `~/.quip-miner/mining_attempts`.

Docker images commonly set `QUIP_RUNTIME_DIR=/data/runtime` so attempts persist on the mounted data volume.

## Layout

```text
{archive_root}/
  {solution_number}/
    attempts-{miner_id}.jsonl
    metadata-{miner_id}.json
    submission.json
    solutions/
      {iter:06d}-{nonce8}
```

Files:

- `attempts-{miner_id}.jsonl`: append-only attempt events from one worker/miner.
- `metadata-{miner_id}.json`: aggregate per solution/miner, rewritten atomically in batches.
- `submission.json`: controller record written when a proof is submitted.
- `solutions/*`: stored/submitted top-5 packed spin configs and energies.

## Solution Number vs Block Number vs dispatch_id

The durable key is **solution number**: `count(QuantumPow.WinningSolutions) + 1` at round start. It is the ordinal of the QPoW solution being mined.

Do not confuse it with:

- **Block number:** `LastProofBlock` is the block that won most recently, not the next solution ordinal.
- **`dispatch_id`:** process-local scheduler/worker coordination handle. It resets on restart and can collide across runs. Never persist artifacts by `dispatch_id`.

A controller/worker restart mid-round should resume writing into the same solution-number directory. That is expected, not stale accretion.

## REST Queries

Attempts:

```bash
curl 'http://127.0.0.1:8086/api/v1/mining/attempts?solution_number=196&limit=1000'
curl 'http://127.0.0.1:8086/api/v1/mining/attempts?miner_id=rig-CPU-1&solution_number=196&limit=1000'
```

Solutions:

```bash
curl 'http://127.0.0.1:8086/api/v1/mining/solutions?solution_number=196'
curl 'http://127.0.0.1:8086/api/v1/mining/solutions?solution_number=196&miner_id=rig-CPU-1'
```

`solution_id` is accepted as an alias for `solution_number`, but prefer `solution_number` in new docs and tools.

## Packed Spin Records

Stored solution records contain `top_5_solutions_hex` and `top_5_energies`. Packed spins are 1 bit per spin. Decode with `numpy.unpackbits`, map `0 -> -1` and `1 -> +1`, and truncate to the topology's node count.
