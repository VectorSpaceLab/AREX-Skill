---
name: persistence-and-evaluation
description: "The persistence-and-evaluation sub-skill routes Faiss index
  storage, clustering, ground-truth evaluation, and bounded operating-point
  experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Persistence and evaluation

Use this branch when the task involves `write_index`/`read_index`, byte
serialization, cloning, mmap or on-disk inverted lists, merging, vector
reconstruction/codes, `Kmeans`, exact ground truth, recall/precision, or
`ParameterSpace` operating points.

## First checks

- Establish `d`, row count, float32 contiguous `(n, d)` arrays, metric, and
  preprocessing before comparing any result. For cosine, normalize both query
  and database arrays and use inner product consistently.
- Treat an index file or serialized byte array as untrusted input. Bound its
  size before reading, use Faiss deserialization limits where available, and
  never deserialize in a privileged or production process without a separate
  trust decision. See [troubleshooting](references/troubleshooting.md).
- Prefer bytes for a bounded in-process handoff and a temporary file followed
  by an atomic rename for a durable artifact. Keep an mmap-backed index alive
  only while its backing file remains present and unchanged.

## Route the work

- Choose the index family and search parameters in
  [index-selection-and-search](../index-selection-and-search/SKILL.md).
- Choose codecs, `sa_encode`/`sa_decode`, and compression constraints in
  [training-and-compression](../training-and-compression/SKILL.md).
- Route ID maps, selectors, refinement, shards, replicas, and ownership to
  [composition-and-filtering](../composition-and-filtering/SKILL.md).
- Route GPU ground truth, CPU/GPU transfer, and backend interoperability to
  [accelerated-and-interoperable](../accelerated-and-interoperable/SKILL.md).

## Operating sequence

1. Build an exact `IndexFlat` baseline with the same metric and preprocessing.
2. Train and populate the candidate only with a bounded, representative
   sample; record `d`, metric, factory/configuration, `ntotal`, and tuning
   parameters alongside results.
3. Measure recall against the exact baseline before and after every operating
   point. Do not use a downloaded benchmark or an unbounded driver for a
   smoke test.
4. Test both `serialize_index`/`deserialize_index` and
   `write_index`/`read_index` when the artifact may cross a process boundary.
5. For a compressed index, distinguish search distance from reconstruction
   error; reconstruction is generally approximate. Use `clone_index` for a
   deep independent CPU copy only after checking that the index type supports
   cloning.
6. Use mmap/OnDisk only when the memory and file-lifetime trade-off is
   intentional. OnDisk additions are slow; build ordinary inverted lists and
   merge them for bulk construction.

The bundled `scripts/smoke_persistence.py` performs a deterministic, tiny CPU
round trip and exact-vs-IVF comparison without downloads or repository paths.
Detailed API facts, recipes, formats, and failure recovery are in the linked
references.
