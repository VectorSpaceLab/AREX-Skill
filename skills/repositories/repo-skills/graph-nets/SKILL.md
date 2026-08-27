---
name: graph-nets
description: "Use DeepMind Graph Nets for GraphsTuple data, TensorFlow graph
  utilities, and Sonnet graph-network modules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Graph Nets

Use this repo skill when a task uses DeepMind Graph Nets (`graph_nets`) to build graph neural networks in TensorFlow/Sonnet, manipulate `GraphsTuple` graph batches, convert NetworkX or NumPy graph data, or debug Graph Nets module and utility errors.

## Read first

- [Repository provenance](references/repo-provenance.md): read before deciding whether this skill is current for a checkout or package version.
- [Compatibility](references/compatibility.md): choose TensorFlow 1/Sonnet 1 versus TensorFlow 2/Sonnet 2, and avoid incompatible NetworkX/TensorFlow stacks.
- [Troubleshooting](references/troubleshooting.md): cross-cutting install/import, dependency, GPU, and version symptoms.
- [Demo recipes](references/demo-recipes.md): distilled guidance from the tutorial, sorting, shortest-path, and physics notebooks without depending on the original notebooks.
- [Install check](scripts/check_graph_nets_install.py): safe JSON diagnostic for an installed `graph_nets` runtime.

## Install and import check

Graph Nets does not declare TensorFlow as a package requirement, so choose a TensorFlow/Sonnet pair explicitly:

```bash
# TF2/Sonnet2-style workflows verified for this skill.
python -m pip install "graph_nets" "tensorflow>=2.2,<2.3" "dm-sonnet>=2,<3" "networkx<3" "protobuf<3.20" "numpy<1.20"

# Legacy TF1/Sonnet1-style workflows verified for this skill.
python -m pip install "graph_nets" "tensorflow>=1.15,<2" "dm-sonnet<2" "tensorflow_probability<0.9" "networkx<2.7" "protobuf<3.20" "numpy<1.20"
```

Then check:

```bash
python - <<'PY'
import graph_nets as gn
from graph_nets import graphs, utils_np, utils_tf, blocks, modules
print("graph_nets import ok")
PY
```

Use the bundled diagnostic when a user reports a version or import problem:

```bash
python path/to/graph-nets/scripts/check_graph_nets_install.py --pretty
```

## Sub-skill routing

| Task signal | Read |
| --- | --- |
| Create, validate, batch, slice, or round-trip `GraphsTuple` data from dictionaries, NumPy arrays, or NetworkX graphs | [graph-data](sub-skills/graph-data/SKILL.md) |
| Use `utils_tf` for tensor `GraphsTuple`s, placeholders/feed dicts, `concat`, `repeat`, fully-connected graphs, padding/masks, `tf.function` signatures, or TF1/TF2 execution choices | [tensorflow-ops](sub-skills/tensorflow-ops/SKILL.md) |
| Build or debug `EdgeBlock`, `NodeBlock`, `GlobalBlock`, `GraphNetwork`, `GraphIndependent`, `InteractionNetwork`, `RelationNetwork`, `DeepSets`, `CommNet`, `SelfAttention`, or demo model factories | [graph-models](sub-skills/graph-models/SKILL.md) |

## Operating checklist

1. **Choose the runtime stack first.** The TF1 stack exposes `tf.Session` and top-level `tf.placeholder`; the verified TF2 stack uses eager tensors and `tf.function` signatures and does not expose those top-level TF1 symbols.
2. **Normalize graph data before modeling.** Use the graph-data sub-skill to enforce `GraphsTuple` field invariants, data dictionary key consistency, and NetworkX feature conventions.
3. **Move into TensorFlow utilities only after data is valid.** Use the TensorFlow ops sub-skill for tensor conversion, padding, masks, session fetchability, or `tf.function` input signatures.
4. **Assemble modules with explicit field assumptions.** Use graph-models when choosing `use_*` flags, reducers, Sonnet factories, or high-level message-passing architecture.
5. **Validate with tiny smoke checks before long demos.** Full notebooks are interactive/training-scale; prefer the bundled scripts and selected native unit tests before attempting notebook reproduction.

## Avoid this skill when

- The task is about JAX graph networks; prefer Jraph or other JAX-specific guidance.
- The task is about PyTorch Geometric, DGL, or generic NetworkX algorithms rather than Graph Nets `GraphsTuple`/TensorFlow/Sonnet APIs.
- The task only edits this repository's packaging or contribution process and does not use Graph Nets as a library; use general Python repository maintenance guidance.
- The task needs a modern TensorFlow/Keras GNN library with maintained TF 2.x APIs; Graph Nets is legacy and may require pinned dependencies.
