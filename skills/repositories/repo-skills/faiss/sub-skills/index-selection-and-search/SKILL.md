---
name: index-selection-and-search
description: "Guides dense-vector metric selection, index construction,
  approximate search tuning, and CPU search validation in Faiss."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Index selection and search

Use this route when the task is to choose or operate a CPU dense-vector index,
compare exact and approximate nearest-neighbor search, or diagnose distance
semantics, result contracts, search tuning, or OpenMP behavior. It covers
float32 dense vectors, L2, inner product, cosine-as-normalized-inner-product,
Flat, IVF-Flat, and graph indexes.

## Route the workflow

1. Normalize the data to a contiguous `float32` matrix of shape `(n, d)` and
   keep database and query dimensions identical. Read
   [the API contract](references/api-reference.md) before calling an index.
2. Choose the smallest index that meets the latency, recall, and memory target.
   Use [the selection and tuning workflows](references/workflows.md) for the
   decision, including the 64D memory-conscious factory case.
3. Build with the lifecycle in the workflow reference: create, train when
   `is_trained` is false, add, then search. Validate against an exact Flat
   baseline before increasing approximation.
4. Use the bundled deterministic helper for a local CPU smoke check:
   `python path/to/skills/disco/faiss/sub-skills/index-selection-and-search/scripts/smoke_search.py --help`.
   It has no downloads and is safe to run from any working directory.
5. For malformed arrays, unavailable methods, empty result ranges, or poor
   recall, follow [troubleshooting](references/troubleshooting.md).

## Boundaries

- Route codecs, binary indexes, PQ/SQ, and compressed-memory choices to
  [training-and-compression](../training-and-compression/SKILL.md).
- Route IDs, selectors, composition, refinement, shards, and replicas to
  [composition-and-filtering](../composition-and-filtering/SKILL.md).
- Route persistence, I/O, clustering, and evaluation tooling to
  [persistence-and-evaluation](../persistence-and-evaluation/SKILL.md).
- Route GPU, cuVS, ROCm, Metal, SVS, and C/C++ interop to
  [accelerated-and-interoperable](../accelerated-and-interoperable/SKILL.md).
- Use the [Faiss root route](../../SKILL.md) for package-wide installation,
  provenance, and cross-workflow routing.
