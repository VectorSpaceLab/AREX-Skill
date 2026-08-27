# CogDL Package Overview

## Purpose

Read this when you need the shortest path into the CogDL repository: what the
package provides, which workflow family owns a request, and which sub-skill to
open next.

## Verified snapshot

- Distribution name: `cogdl`
- Public import name: `cogdl`
- Version observed in the inspected checkout: `0.6`
- Main entry points: `experiment(...)` and `pipeline(...)`
- Core graph objects: `Graph`, `Adjacency`, `Dataset`, `NodeDataset`, `GraphDataset`, `DataLoader`
- Core training object: `Trainer`
- Public application registry: `dataset-stats`, `dataset-visual`, `generate-emb`, `oagbert`, `recommendation`
- The repository also exposes a large model registry and many built-in datasets; check the dedicated sub-skill references for the full lists.

## What CogDL is good at

CogDL combines graph data abstractions, model/layer registries, a unified trainer,
and application-style pipelines. Common user-facing work falls into five groups:

| Workflow family | Typical request signals | Best entry point |
| --- | --- | --- |
| Experiment/CLI | `experiment`, `scripts/train.py`, `--dataset`, `--model`, `--cpu`, `--devices`, `search_space` | `sub-skills/experiments-and-cli/` |
| Graph data and datasets | `Graph`, `NodeDataset`, `GraphDataset`, masks, batching, built-in dataset names | `sub-skills/graph-data-and-datasets/` |
| Models/layers/operators | `GCNLayer`, `GATLayer`, `BaseModel`, sparse operators, custom GNNs | `sub-skills/models-layers-and-operators/` |
| Trainer/wrappers | `Trainer`, `mw`, `dw`, checkpointing, logging, `use_best_config` | `sub-skills/training-wrappers-and-customization/` |
| Pipeline apps | `pipeline()`, dataset stats, visualization, embeddings, recommendation, OAG-BERT | `sub-skills/pipelines-and-applications/` |

## High-level package shape

- `cogdl.experiments` owns the high-level experiment orchestration and AutoML
  path.
- `cogdl.options` builds the parser-backed namespaces used by both API and CLI
  training flows.
- `cogdl.data` and `cogdl.datasets` own graph objects and dataset loaders.
- `cogdl.models`, `cogdl.layers`, and `cogdl.operators` own model selection,
  layers, and sparse/message operators.
- `cogdl.trainer` and `cogdl.wrappers` own the unified training loop and its
  wrapper matching logic.
- `cogdl.pipelines` owns the named application routes.
- `cogdl.oag` owns OAG-BERT model loading and paper/entity helpers.

## Installation stance

Use the package after installing a compatible PyTorch build. For local inspection,
`pip install -e .` from the repository root is the default. The repository's
runtime dependencies already include the main Python packages used by the public
APIs, but OGB and OAG-BERT still have optional network/cache implications:

- `ogb` for OGB datasets and benchmark helpers
- `transformers` and `sentencepiece` for OAG-BERT model families

## What to read next

- `references/troubleshooting.md` when import, dependency, dataset-download, or
  optional backend issues appear.
- `references/repo-provenance.md` before checking staleness or refreshing the
  skill for a newer checkout.
- The most relevant sub-skill when the task is actually about using CogDL rather
  than learning the package shape.
