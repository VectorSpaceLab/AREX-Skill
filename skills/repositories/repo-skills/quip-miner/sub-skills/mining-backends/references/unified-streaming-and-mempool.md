# Unified Streaming and Mempool Architecture

Every backend and both job types mine through the same pipeline:

```text
L1 Orchestrator: chain head + submit
    dispatches switch commands with job kind and feeder spec
L2 Worker/coordinator: owns a SampleView over a shared-memory ring
    consumes descriptor queue entries and evaluates/ratchets/stashes results
L3 Stream-driver subprocess: owns backend sampler + feeder
    writes samples into shared-memory ring slots and sends descriptors back
```

There is no synchronous inline sampling path.

## Per-backend Factories

Each backend exposes a persistent context factory used only in the stream-driver process:

| Backend | Factory area |
| --- | --- |
| CPU SA | `CPU.sa_stream` |
| CUDA | `GPU.cuda_stream` |
| Metal | `GPU.metal_stream` |
| Modal | `GPU.modal_stream` |
| D-Wave QPU | `QPU.dwave_miner` |

The common `StreamContext` is backend- and job-agnostic. The sampler differs by backend; the feeder differs by job kind.

## Sampler Contract

Backends implement a streaming sampler shape equivalent to:

```python
sample_ising_streaming(feeder, *, num_reads, num_sweeps, **sampler_kwargs)
```

It yields `(model, sampleset)` for each completed model. A generator must catch `StopIteration` from `feeder.pop_blocking()` and return cleanly; letting `StopIteration` escape a generator body becomes `RuntimeError` under PEP 479.

## Feeder Specs

The `switch` command carries a picklable feeder spec:

- PoW: `("pow", last_proof_block_hash, miner_bytes)` creates or reseeds a `RandomIsingFeeder`.
- Mempool: `("mempool", problemview_attach_args, slot)` creates a `FixedIsingFeeder` backed by a one-slot shared problem view.

This is why mempool and PoW share the same workers instead of separate code paths.

## QPU Specifics

The QPU sampler keeps a queue of async submissions, yields raw reduced samplesets, and attaches `DefectInfo` for worker-side correction/reconstruction. Reconstruction is done in the worker after a cheap pre-check, not in the D-Wave connection path.

## Mempool Scheduling

- CPU/GPU: mempool defaults on and can preempt PoW on the same workers.
- QPU: mempool defaults off; when opted in, jobs dispatch idle-only and never interrupt in-flight paid QPU work.
- A fatal mempool submit receipt parks mempool for the run while PoW continues.
- Solver registration is automatic at startup for the elected owner group.

## No-inline-sampling Guard

Maintainer checks must keep these deleted symbols out of production source:

- `def _sample(`
- `def _sample_batch(`
- `STREAMING_PUMP`
- `DRIVER_OWNS_FEEDER`

Run the bundled maintainer script when changing sampling code:

```bash
python ../maintainer-testing-release/scripts/lint_no_inline_sampling.py --repo-root <checkout>
```
