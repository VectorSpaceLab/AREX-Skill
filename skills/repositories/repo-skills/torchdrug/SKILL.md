---
name: torchdrug
description: "Route TorchDrug graph learning, drug discovery, molecular ML,
  protein, knowledge graph, data, model, and training engine workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchDrug

Use this repo skill when a task involves TorchDrug, TorchProtein, graph neural networks for drug discovery, molecular property prediction, molecular generation, retrosynthesis, protein workflows, knowledge graph completion, or TorchDrug's `core.Engine` training stack.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a TorchDrug checkout or package version.
- Read [references/troubleshooting.md](references/troubleshooting.md) for install/import, PyTorch/PyG compiled packages, RDKit, data downloads, GPU, `mps`, and package-version pitfalls.
- Run `python scripts/check_torchdrug_env.py` in the user's TorchDrug environment for a no-download import and capability check.

## Install And Verify

TorchDrug 0.2.1 supports Python `>=3.7,<3.11` and PyTorch `>=1.8.0`. Prefer a fresh environment with Python 3.10 or earlier:

```bash
python -m pip install torchdrug
python - <<'PY'
import torchdrug
from torchdrug import data
print(torchdrug.__version__)
graph = data.Graph([[0, 1], [1, 0]], num_node=2)
print(graph.num_node, graph.num_edge)
PY
```

When installing from pip, install PyTorch first, then choose `torch-scatter` and `torch-cluster` wheels that match the PyTorch and CUDA/CPU build. Conda users can prefer the documented conda channels because they solve PyTorch, PyG, RDKit, and compiled packages together.

## Route By Task

| User task | Read |
| --- | --- |
| Graph, molecule, protein, dataset, SMILES, sequence, packing, masking, splitting, collator, or data validation tasks | [sub-skills/graph-data/SKILL.md](sub-skills/graph-data/SKILL.md) |
| Choosing or customizing graph layers, representation models, readouts, samplers, variadic tensor utilities, or `MessagePassingBase` subclasses | [sub-skills/layers-and-extensions/SKILL.md](sub-skills/layers-and-extensions/SKILL.md) |
| Building `core.Engine` loops, checkpointing, config serialization, logging, CPU/GPU settings, task contracts, or training harnesses | [sub-skills/training-engine/SKILL.md](sub-skills/training-engine/SKILL.md) |
| Molecular property prediction, molecular pretraining, generation with GCPN/GraphAF, or USPTO50k retrosynthesis | [sub-skills/molecular-workflows/SKILL.md](sub-skills/molecular-workflows/SKILL.md) |
| Knowledge graph triples, FB15k/WN18/YAGO/Hetionet, TransE/RotatE/NeuralLP/KBGAT, negative sampling, or filtered ranking | [sub-skills/knowledge-graphs/SKILL.md](sub-skills/knowledge-graphs/SKILL.md) |
| Protein sequences/structures, contact prediction, GearNet, ESM, protein property/function, or protein-protein interaction workflows | [sub-skills/protein-workflows/SKILL.md](sub-skills/protein-workflows/SKILL.md) |

## Common Workflows

- For a tiny in-memory smoke test, route to `graph-data` and run its `scripts/smoke_graph_data.py` helper.
- For a new molecular prediction project, combine `graph-data` for the molecule dataset, `molecular-workflows` for task/model choices, and `training-engine` for `core.Engine` save/load.
- For custom graph neural layers, use `layers-and-extensions` first, then return to `training-engine` to wire the module into a task.
- For protein GearNet or ESM tasks, use `protein-workflows` for data/model/task choices and `layers-and-extensions` only for graph construction internals.
- For knowledge graph reasoning, use `knowledge-graphs` for model/task/dataset decisions and `training-engine` for optimizer, evaluation, and checkpoint details.

## Safety Boundaries

- Do not run dataset downloads, long training, retrosynthesis generation, benchmark sweeps, or ESM weight downloads unless the user allows network, storage, and compute cost.
- Do not assume `gpus=[0]` is valid. Use `gpus=None` for CPU-only work and check `torch.cuda.is_available()` before GPU examples.
- Do not use Apple `mps`; TorchDrug documentation says Apple silicon can run on CPU but `mps` is unsupported.
- Do not tell users to open original TorchDrug docs, tests, or examples as runtime requirements. This skill bundles the needed routes, references, and safe helpers.

## Repository Scope

This skill covers public TorchDrug package usage and repo-derived workflows: source APIs under `torchdrug/`, install metadata, Sphinx docs, tutorials, benchmarks, and representative tests. It intentionally does not cover maintainer release automation, full benchmark reproduction, or external dataset/model-weight acquisition beyond documented prerequisites.
