---
name: ogb
description: "Routes OGB graph dataset, evaluator, conversion, and export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# OGB

Use this skill for the Open Graph Benchmark package when the task is about
loading OGB datasets, choosing an evaluator, converting molecules or code into
OGB graphs, or packaging a new OGB-style dataset.

## Read this skill when

- The request names `ogb`, `ogbg-*`, `ogbn-*`, `ogbl-*`, `PCQM4M`,
  `MAG240M`, `WikiKG90M`, or `DatasetSaver`.
- The task asks for `GraphPropPredDataset`, `NodePropPredDataset`,
  `LinkPropPredDataset`, `PCQM4MDataset`, `PCQM4Mv2Dataset`,
  `MAG240MDataset`, `WikiKG90MDataset`, or the matching evaluator.
- The task mentions `smiles2graph`, `py2graph`, `meta_dict.pt`, `mapping/`,
  `split_dict.pt`, `test-dev`, `test-challenge`, or OGB submission files.
- The task asks for PyG or DGL dataset wrappers and the corresponding backend
  packages are installed.

## Install

```bash
python -m pip install -e .
```

If you need the molecular helper, install `rdkit` as well. If you need the PyG
or DGL wrapper classes, install the matching optional backend package too.

## Start here

1. Read [`references/api-overview.md`](references/api-overview.md) for the
   public class map and the common loader/evaluator shapes.
2. Read [`references/installation.md`](references/installation.md) for the
   package install command and the optional backend notes.
3. Read [`references/dataset-catalog.md`](references/dataset-catalog.md) when
   you need the exact dataset names or metrics.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   imports fail, downloads are interrupted, or shapes do not match.

## Route by task family

- Use [`sub-skills/graph-property-prediction/SKILL.md`](sub-skills/graph-property-prediction/SKILL.md)
  for `ogbg-*`, molecular graph workflows, `smiles2graph`, and `ogbg-code2`.
- Use [`sub-skills/node-property-prediction/SKILL.md`](sub-skills/node-property-prediction/SKILL.md)
  for `ogbn-*` datasets and node-level evaluators.
- Use [`sub-skills/link-property-prediction/SKILL.md`](sub-skills/link-property-prediction/SKILL.md)
  for `ogbl-*` datasets, ranking metrics, and knowledge-graph completion.
- Use [`sub-skills/lsc-benchmarks/SKILL.md`](sub-skills/lsc-benchmarks/SKILL.md)
  for PCQM4M, MAG240M, WikiKG90M, submission files, and large-scale
  benchmark notes.
- Use [`sub-skills/dataset-contribution/SKILL.md`](sub-skills/dataset-contribution/SKILL.md)
  for `DatasetSaver` and OGB-compatible dataset packaging.

## Quick install check

After installing the package, run the bundled smoke helper:

```bash
python scripts/check-install.py
```

If you need the molecule helper, also run:

```bash
python scripts/smiles2graph-smoke.py
```

## What this skill does not do

- It does not tell you to run the original repository's heavy training examples
  as the runtime skill.
- It does not depend on the source checkout remaining available once the skill
  is generated.
- It does not treat the vendored WikiKG90M external framework tree as bundled
  runtime content.

## Useful bundled helpers

- [`scripts/check-install.py`](scripts/check-install.py): verifies the installed
  package, optional backend presence, and core imports.
- [`scripts/list-datasets.py`](scripts/list-datasets.py): prints the dataset
  catalog from the installed package metadata.
- [`scripts/smiles2graph-smoke.py`](scripts/smiles2graph-smoke.py): runs a tiny
  molecule-to-graph smoke check.

## Provenance and routing

Read [`references/repo-provenance.md`](references/repo-provenance.md) to see
which repo state this skill was distilled from, and
[`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
for the router scenario metadata used during import.
