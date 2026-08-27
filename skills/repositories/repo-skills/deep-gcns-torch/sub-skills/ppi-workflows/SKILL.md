---
name: ppi-workflows
description: "Operate the DeepGCNs PPI node-classification workflow with exact
  train/test flags, residual/plain/dense architecture choices, PyG loader and
  DataParallel boundaries, micro/macro F1 semantics, and checkpoint alignment
  without downloading data or running full training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PPI workflows

Use this skill for the source-evidenced protein-protein interaction (PPI) node
classification workflow, including its residual/plain/dense backbones and
F1-based evaluation. This is a reference-only operating skill. The original
source example is evidence only, not a runtime dependency: use only a
caller-supplied PPI entry point and staged local inputs. Do not copy or launch
the full training program, download PPI data, fetch external-drive checkpoints,
or claim that a CPU smoke reproduces the published GPU result.

## Route first

- **PPI node classification**: read [workflows.md](references/workflows.md),
  then validate the data and metric contract in
  [data-and-metrics.md](references/data-and-metrics.md).
- **Generic GraphConv, EdgeConv, MRConv, GAT/GIN/GCN/SAGE construction, KNN,
  GENConv, or block API questions**: route to the sibling
  [graph-layers](../graph-layers/SKILL.md) skill. Keep this skill's architecture
  choices at the task level.
- **OGB proteins or another OGB benchmark**: route to
  [ogb-workflows](../ogb-workflows/SKILL.md). OGB proteins is not the PyG PPI
  dataset and does not share its split, feature, label, or checkpoint
  conventions.
- **ModelNet40, S3DIS, PartNet, or point-cloud layouts**: route to the sibling
  point-cloud workflow skill.

## Safe operating sequence

1. Establish the requested phase (`train` or `test`), prepared local data root,
   feature and label dimensions, device/backend, loader mode, architecture
   tuple (`block`, `conv`, `n_filters`, `n_blocks`, and `n_heads`), and checkpoint
   path if any.
2. Verify that the data and checkpoint were staged by the caller. The upstream
   PyG dataset can auto-download when files are absent, but this skill never
   permits that side effect. Do not run a download or embed a downloader.
3. Check the exact flags and source-observed defaults in
   [workflows.md](references/workflows.md). In particular, do not rely on the
   README's prose default for filter width: the parser's default is authoritative
   for the source workflow.
4. Align the checkpoint basename and tensor shapes with the requested model
   before loading. A checkpoint is not interchangeable merely because it is
   labelled `ppi`.
5. Prefer a tiny, local, synthetic forward/parser check when validating an
   environment. Treat full PPI training, validation, and benchmark numbers as
   GPU/data/checkpoint-dependent prerequisites, not as bundled actions.
6. Report micro F1 separately from macro F1. The source path computes micro F1
   only; it does not produce macro F1.

## Operating invariants

- PPI examples use static sparse graph convolutions over PyG `edge_index`.
  Node features have shape `[num_nodes, num_features]`; output logits have
  shape `[num_nodes, num_classes]`. The model obtains `data.batch`, but the
  static PPI forward path does not use it to construct a graph.
- The standard PyG PPI contract is 50 floating-point node features and 121
  binary gene-ontology labels. `n_classes` is inferred from the test dataset;
  it is not a CLI flag.
- The loss is `BCEWithLogitsLoss`. A positive prediction is formed by testing
  the raw logit with `out > 0`, equivalent to a sigmoid threshold of 0.5.
- The documented score is micro F1 (`average="micro"`) over multilabel node
  predictions. Macro F1 (`average="macro"`) is a different statistic and must
  not be inferred from the source's `mF1`/`m-F1` log label.
- Checkpoint architecture identity is
  `ppi-{block}-{conv}-{n_blocks}-{n_filters}`, optionally followed by
  `-{postname}`. The phase suffix is `_val_best` or `_test_best`; see the
  checkpoint section in the references for the save-directory date component.
- `--multi_gpus` selects PyG `DataListLoader` for training and wraps the model
  with PyG `DataParallel`. The source constructs ordinary `DataLoader` objects
  for validation/test, so multi-GPU evaluation is a compatibility boundary and
  must be checked rather than assumed.

## Scope boundary

The references preserve exact source-observed commands, flags, data fields,
metric behavior, checkpoint naming, and failure modes without bundling the
training implementation. No PPI configuration checker is included: the
parser has source-era boolean and path behavior, while a safe checker that
faithfully validates data/checkpoint contents would either duplicate the
training stack or invite data access. This explicit reference-only choice keeps
the runtime tree offline-safe and makes the unsupported parts visible.
