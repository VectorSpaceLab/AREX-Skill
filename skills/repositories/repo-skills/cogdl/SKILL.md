---
name: cogdl
description: "Routes CogDL graph-learning workflows for experiments, graph data,
  models, training wrappers, and pipeline apps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CogDL

CogDL is a graph deep learning toolkit for node classification, graph classification,
link prediction, graph embedding, heterogeneous graphs, traffic prediction,
and application-style pipelines such as dataset inspection and OAG-BERT.

Use this root router when a user asks about CogDL itself, names one of its public
APIs, or needs help choosing which part of the package to open first.

## Quick start

1. Install PyTorch first with a CPU or CUDA wheel that matches the host.
2. Install CogDL in editable mode for local inspection:

```bash
pip install -e .
```

3. For a published wheel instead of a checkout install, use:

```bash
pip install cogdl
```

4. If the task needs optional package families, add them explicitly:
   - `ogb` for OGB datasets and benchmarks
   - `transformers` and `sentencepiece` for OAG-BERT
   - the repo already declares `optuna`, `gensim`, `grave`, `tabulate`, `numba`,
     and `ninja` as runtime dependencies

## Minimal import check

```bash
python -c "import cogdl; from cogdl import experiment, pipeline; print(cogdl.__version__)"
python scripts/check_cogdl_environment.py --show-registries
```

Use `python -m pip check` after install to catch incompatible dependencies.

## Route map

- `sub-skills/experiments-and-cli/`: `experiment()`, `get_default_args`, CLI flags,
  `scripts/train.py`, variants, checkpoint/log/embedding flags, and AutoML.
- `sub-skills/graph-data-and-datasets/`: `Graph`, `Adjacency`, `Dataset`,
  `NodeDataset`, `GraphDataset`, `DataLoader`, masks, schemas, and tiny fixtures.
- `sub-skills/models-layers-and-operators/`: model registry, layers, custom GNNs,
  and sparse/message operators.
- `sub-skills/training-wrappers-and-customization/`: `Trainer`, wrappers,
  default wrapper matching, configs, checkpoint/resume, and logging.
- `sub-skills/pipelines-and-applications/`: `pipeline()` apps, embedding
  generation, recommendation, and OAG-BERT.

## Shared references

Read these before refreshing the skill or checking whether a checkout is current:

- `references/package-overview.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md`

## Shared smoke script

Run `scripts/check_cogdl_environment.py` when you want a fast, no-download check
of the installed package, registry counts, and optional CUDA/Graph smoke probes.

## Scope notes

- Built-in datasets may download or populate caches on first use.
- OAG-BERT weights and archives are optional, cache- or network-dependent
  resources.
- CUDA acceleration is optional in this skill tree; CPU-safe workflows are the
  baseline unless a sub-skill explicitly says otherwise.
- For maintainer-only repository edits, CI, or release tasks, use a different
  workflow; this runtime skill is for research-side usage.
