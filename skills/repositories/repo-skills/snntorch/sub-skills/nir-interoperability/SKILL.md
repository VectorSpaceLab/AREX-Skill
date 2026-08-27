---
name: nir-interoperability
description: "Export snnTorch models to NIR and import NIR graphs back into snnTorch."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# nir-interoperability

Use this sub-skill when the task is specifically about NIR export/import.

## Use this sub-skill for
- exporting supported snnTorch models to NIR
- importing NIR graphs back into snnTorch
- checking sequential or recurrent NIR round-trips
- validating bundled NIR fixtures and compatibility edge cases

## Keep out of scope
- spike encodings and target coding
- training loops and optimization
- plotting and animation
- dataset loading beyond what is needed to build a tiny NIR fixture

## Core contract
- `sample_data` is the trace input used to infer graph shapes.
- `ignore_dims` trims dimensions from traced shapes; use it for batch-first tensors.
- Sequential graphs round-trip through a plain NIR graph.
- Simple recurrent graphs round-trip as an embedded NIR subgraph.
- Use vector-shaped `beta`, `alpha`, `threshold`, and recurrent `V` values that match the neuron width.

## Bundled helpers
- `scripts/nir_roundtrip_smoke.py` — self-contained export/import smoke test
- `references/fixtures/lif.nir` — minimal import fixture
- `references/fixtures/conv_pool_limit.nir` — current conv/pool compatibility reference

For signatures, node mappings, workflow steps, and known failure modes, see the bundled references.
