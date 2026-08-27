---
name: backends-and-storage
description: "Choose, configure, validate, and troubleshoot LEANN vector
  backends, index artifacts, and selective embedding recomputation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Backends and storage

Use this sub-skill when the task changes the vector index backend, storage mode,
search graph, optional accelerator, or recomputation path. Keep ordinary
embedding/provider and end-to-end API/CLI instructions in their sibling
sub-skills.

## Route by decision

1. Choose a backend or plan an update: [backend selection](references/backend-selection.md).
2. Identify files, passage offsets, or recomputation behavior:
   [artifacts and recomputation](references/index-artifacts-and-recomputation.md).
3. Tune graph/IVF search, pruning, beam, or metric compatibility:
   [backend tuning](references/backend-tuning.md).
4. Evaluate DiskANN or CUDA FlashLib variants:
   [optional accelerator backends](references/optional-accelerator-backends.md).
5. Diagnose a failed install, build, search, or incomplete index:
   [troubleshooting](references/troubleshooting.md).
6. Validate an existing index without changing it:
   `python scripts/inspect_leann_index.py INDEX_PATH`.

## Non-negotiable invariants

- The installed distribution names (`leann-backend-*`) and registry names are
  different; use the exact registry name in LEANN configuration.
- The embedding dimension and distance metric recorded in `.meta.json` must
  agree with the vectors and backend artifact. Normalized vectors need the
  cosine-compatible path described in the tuning reference.
- Compact/pruned HNSW is a storage format, not an update format: it requires
  recomputation for search and must be rebuilt for in-place changes.
- IVF is the CPU modification-oriented option: it uses FAISS `IndexIVFFlat`
  with `DirectMap.Hashtable`, and updates remove old IDs before adding new ones.
- DiskANN and both FlashLib variants are optional in this verified environment;
  never turn their documentation into a local availability or performance
  promise. The inspector checks files only and does not prove native/GPU search.

The bundled inspector is read-only, uses no model/network/credential, and exits
nonzero for invalid metadata, passage-offset mappings, or required backend
artifacts. See the references for the exact checks and known limits.
