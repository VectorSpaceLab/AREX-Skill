---
name: einops
description: "Use the einops Python package for readable tensor rearrangement,
  reductions, repetition, named-axis einsum, packing, framework layers, and
  repository maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# einops Repo Skill

Use this repo skill when a task involves the `einops` Python package: readable
and shape-checked tensor manipulation, named axes, deep-learning tensor
refactors, reversible token/feature packing, optional framework layers, or
maintainer workflows for the einops repository.

## Install and Minimal Check

Public package install:

```bash
pip install einops
```

`einops` declares no runtime dependencies. Install NumPy, PyTorch, TensorFlow,
JAX, or another tensor framework separately according to the user's project.
For a minimal core check with NumPy installed:

```python
import numpy as np
from einops import rearrange, reduce, repeat

x = np.arange(2 * 3 * 4).reshape(2, 3, 4)
assert rearrange(x, "batch channel time -> batch time channel").shape == (2, 4, 3)
assert reduce(x, "batch channel time -> batch time", "sum").shape == (2, 4)
assert repeat(x, "batch channel time -> batch channel time copy", copy=2).shape == (2, 3, 4, 2)
```

For a bundled diagnostic, run
[`scripts/check_einops_install.py`](scripts/check_einops_install.py) after
installing `einops` and, for the full smoke, `numpy`.

## Route Map

- [`sub-skills/tensor-operations/`](sub-skills/tensor-operations/SKILL.md):
  use `rearrange`, `reduce`, `repeat`, `parse_shape`, and `asnumpy` for core
  tensor shape transformations, pooling, broadcasting, stack/concatenate,
  ellipsis, and pattern troubleshooting.
- [`sub-skills/named-einsum-and-packing/`](sub-skills/named-einsum-and-packing/SKILL.md):
  use `einsum`, `pack`, and `unpack` for named-axis contractions, attention-like
  dot products, class-token/multimodal packing, packed-shape (`PS`) handling,
  and reversible split/merge workflows.
- [`sub-skills/framework-integrations/`](sub-skills/framework-integrations/SKILL.md):
  use optional backend dispatch, Array API functions, framework layers,
  `EinMix`, torch scripting/compilation notes, and missing optional dependency
  diagnostics.
- [`sub-skills/repo-development/`](sub-skills/repo-development/SKILL.md):
  use maintainer guidance for focused tests, backend selection,
  `EINOPS_TEST_BACKENDS`, docs/notebook checks, formatting/type checks, CI
  matrix interpretation, and release/deploy boundaries.

## Core Decision Points

- If the user wants a readable replacement for `reshape`, `view`, `permute`,
  `transpose`, pooling, tiling, broadcasting, or shape parsing, start with
  `tensor-operations`.
- If the operation is a mathematical contraction or a dot product with named
  axes, use `named-einsum-and-packing` and remember that `einops.einsum` takes
  tensors first and the pattern last.
- If multiple tensors must be concatenated and later split without losing their
  heterogeneous middle dimensions, use `pack`/`unpack` rather than manual slices.
- If the transform belongs inside a neural-network model definition, serialized
  layer, Keras model, Flax module, or Torch `Sequential`, use
  `framework-integrations`.
- If the task is about changing the repository, running native tests, or
  building docs, use `repo-development` instead of package-usage routes.

## Shared References

- [`references/repo-provenance.md`](references/repo-provenance.md): source
  commit, tag, package version, evidence paths, and refresh cues.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json):
  structured scenario metadata for DisCo repo-skill routing if imported later.
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting
  install/import, optional dependency, backend, and stale-skill troubleshooting.

## Safe Operating Rules

- Keep runtime guidance self-contained. Do not require future agents to open or
  run original repository notebooks, tests, docs, or scripts to complete normal
  package-usage tasks.
- Treat optional frameworks as optional. A CPU NumPy smoke does not prove CUDA,
  ROCm, MPS, TensorFlow, JAX, or PyTorch runtime behavior.
- Prefer explicit semantic axis names (`batch`, `channel`, `height`, `width`) in
  examples that explain user intent.
- When decomposing axes such as `(height h2)`, supply or validate lengths that
  cannot be inferred safely.
- For maintainer commands that can mutate an environment or docs tree, use the
  repo-development sub-skill's dry-run helpers before executing.

## Refresh Triggers

Read `references/repo-provenance.md` before deciding this skill is current for a
checkout. Refresh the repo skill if the package version, public API exports,
pattern grammar, backend list, layer modules, native test runner, docs scripts,
CI matrix, or relevant evidence paths changed since the recorded snapshot.
