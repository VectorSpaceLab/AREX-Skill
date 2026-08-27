---
name: training-and-compression
description: "This skill teaches a Researcher to train, compose, inspect, and
  troubleshoot Faiss compressed and binary indexes while preserving codec,
  dimension, and backend constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and compression

Use this branch when the request involves **training or adding compressed
codes**, PQ/SQ/IVF-PQ, residual or additive quantization, RaBitQ, OPQ and
other transforms, PQ fast scan, standalone codecs, reconstruction, code size,
or binary/Hamming indexes. The CPU baseline is the verified Faiss 1.15.0
package (Python >=3.10, NumPy float32 arrays, `OPTIMIZE DD AVX2`). Treat every
CUDA, cuVS, ROCm, Metal, or SVS claim as conditional until the runtime probe
in the accelerated sibling succeeds.

## Route first

- For generic exact-versus-approximate index choice, metrics, `nprobe`, and
  search behavior, read [index-selection-and-search](../index-selection-and-search/SKILL.md).
- For `IndexPreTransform`, ID ownership, selectors, and `IndexRefine*`
  composition, read [composition-and-filtering](../composition-and-filtering/SKILL.md).
- For persistence, ground truth, recall measurement, and benchmark/evaluation
  design, read [persistence-and-evaluation](../persistence-and-evaluation/SKILL.md).
- For GPU-resident codecs or CPU/GPU transfer, read
  [accelerated-and-interoperable](../accelerated-and-interoperable/SKILL.md).

This branch owns the codec lifecycle and the compressed representation. It
does not choose a general index family, own custom IDs/selectors, or certify
optional accelerators.

## Operating procedure

1. Normalize the input as a contiguous `float32` matrix of shape `(n, d)` for
   float indexes, or a contiguous `uint8` matrix of shape `(n, d // 8)` for
   binary indexes. Binary dimension must be a multiple of eight; do not pass
   unpacked boolean/float bits to an `IndexBinary`.
2. Select a factory or explicit class only after checking the constraints and
   code-size formulas in [api-reference.md](references/api-reference.md).
   Keep metric and transform dimensions consistent through the whole chain.
3. Keep a representative, finite training sample separate from the database.
   Call `train(training_vectors)` before `add(database_vectors)` whenever
   `is_trained` is false. Training data needs enough examples for the coarse
   centroids and every codec; a small smoke may warn, but production training
   should not ignore those warnings.
4. Add only vectors with the input dimension expected by the outer index. For
   an IVF codec, Faiss trains the coarse quantizer and encoder as part of the
   outer lifecycle; do not manually add to an untrained IVF-PQ/SQ index.
5. Search with a deliberately chosen `nprobe` (IVF) and `k`; then measure
   against an exact baseline before trading bits, subquantizers, or probes.
   Compression changes recall and reconstructed values even when the API
   succeeds.
6. If a caller needs bytes, use `sa_encode`/`sa_decode` with `uint8` arrays of
   exactly `sa_code_size()` columns. `reconstruct` and decoded values are
   approximations for lossy PQ/SQ/RQ/AQ/RaBitQ codecs; they are not the
   original vectors. RaBitQ's `sa_decode` is suitable for its IP-oriented
   codec representation but is explicitly not a reliable L2 reconstruction
   oracle; use its search path for L2.
7. For a recall/latency compromise, first improve the candidate set (for
   example IVF `nprobe`), then add a refinement stage owned by the composition
   sibling. Refinement requires a compatible reconstructable/exact storage
   choice and must not be used to hide an untrained or dimension-invalid base
   index.
8. Run the bundled no-network check when validating a small configuration:

   ```bash
   python /path/to/training-and-compression/scripts/smoke_codecs.py --help
   python /path/to/training-and-compression/scripts/smoke_codecs.py
   ```

   It uses deterministic tiny data and returns nonzero for invalid factory,
   dimension, metric, or binary input. It is a smoke, not a benchmark.

## Fast scan and optional features

PQ/AQ fast scan is a storage/layout specialization, not a replacement for
training or recall evaluation. The verified family is 4-bit PQ/AQ with a
block size divisible by 32 (default 32); it repacks codes into blocks and may
pad the final block. SIMD dispatch can select a different implementation or a
scalar fallback. Do not infer that a fast-scan factory is available merely
because the host has a GPU or because an unrelated SIMD level is present.

Residual, additive, product-residual, LSQ, and RaBitQ families expose more
parameters than the compact examples here. Use the API and workflow tables,
then run a tiny CPU trial before adopting one. GPU codec behavior belongs to
the accelerated sibling and is unverified by this CPU branch.

## Recovery routing

For invalid `IVF...`/PQ strings, wrong `d % M`, too few training points,
unsupported fast-scan blocks, bad byte shapes, or reconstruction surprises,
start with [troubleshooting.md](references/troubleshooting.md). Preserve the
original failing configuration and error; repair one constraint at a time.
For a high-level factory replacement route to the index-selection sibling,
for staged refinement route to composition, and for recall/memory evidence
route to persistence-and-evaluation.

## Bundled references

- [API and representation reference](references/api-reference.md)
- [Training and comparison workflows](references/workflows.md)
- [Troubleshooting and recovery](references/troubleshooting.md)
- [Deterministic codec/binary smoke](scripts/smoke_codecs.py)
