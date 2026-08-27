---
name: ogb-workflows
description: "Run and adapt the repository's OGB node, graph, and link benchmark
  workflows with DeeperGCN/GENConv, partitioned or batched data, feature
  encoders, reversible proteins models, and the optional DGL RevGAT
  teacher/student path. Use this skill for OGB task configuration, checkpoint
  contracts, memory boundaries, and safe synthetic validation; route generic
  layer APIs to graph-layers, PPI to ppi-workflows, and point-cloud tasks to
  point-cloud-workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OGB workflows

Use this skill when the request names OGB, `ogbn-*`, `ogbg-*`, `ogbl-collab`,
DeeperGCN, GENConv, RevGNN, RevGAT, or graph knowledge distillation. It is an
operating guide for the documented workflows, not a promise to download data or
reproduce a large benchmark in the current session.

## Route first

- **Node classification:** `ogbn-arxiv` is full-batch; `ogbn-products` uses
  random induced partitions; `ogbn-proteins` uses partitioning and edge-derived
  initial features. Use [ogb-tasks.md](references/ogb-tasks.md).
- **Graph property prediction:** `ogbg-molhiv`, `ogbg-molpcba`, and `ogbg-ppa`
  use PyG graph batches, categorical/edge feature handling, and graph pooling.
- **Link prediction:** `ogbl-collab` uses a full node encoder plus a batched
  MLP link predictor and Hits@10/50/100 evaluation.
- **Memory-efficient proteins:** use [reversible-ogb.md](references/reversible-ogb.md)
  only when the user explicitly needs the RevGCN backbone or depth/memory tradeoff.
- **DGL RevGAT:** optional and separately gated; it needs a DGL-compatible CUDA
  environment. Do not substitute it for the PyG GENConv workflows.
- Route a request about a layer constructor, aggregation implementation,
  KNN, or generic reversible primitive to **graph-layers**. Route PPI to
  **ppi-workflows** and point-cloud datasets to **point-cloud-workflows**.

## Safe operating sequence

1. Confirm dataset, task type, metric, device, available cached data, and
   checkpoint availability. A CPU model smoke does not establish large-graph
   memory or benchmark accuracy.
2. Start with the task-specific defaults and change only the flags needed by
   the requested comparison. The task parsers use `conv=gen`; the live
   `GENConv` API defaults are documented in the references and are not always
   identical to task-parser defaults.
3. Prepare the data without implicit network access. OGB constructors may
   download when data is absent; stop and ask for an approved, already-cached
   dataset location rather than allowing a bundled helper to fetch it.
4. Use the command shape only from the task reference. Native task modules use
   directory-local imports; an independently staged implementation must provide
   an equivalent task-local entrypoint rather than relying on arbitrary dotted
   imports.
5. Save and load the complete checkpoint expected by the task. Check the model
   and predictor separately for `ogbl-collab`; use `model_state_dict` from the
   repository's standard training checkpoints. Never infer a result from a
   checkpoint whose architecture flags differ.
6. For a bounded check, run `scripts/ogb_model_smoke.py --help` and then its
   tiny synthetic validation. It never creates a dataset, accesses a network,
   or loads a checkpoint.

## GENConv and block choices

The task models use sparse `GENConv` inside `plain`, `res`, or `res+` blocks;
`dense` is advertised by some parsers but the OGB model implementations raise
`NotImplementedError`. The important knobs are `--gcn_aggr`, `--t`, `--p`,
`--y`, `--learn_t`, `--learn_p`, `--learn_y`, `--msg_norm`,
`--learn_msg_scale`, `--norm`, and `--mlp_layers`. Edge-aware molecular and
protein models additionally use `--conv_encode_edge`; molecular models use
`--add_virtual_node` and `--graph_pooling`.

Do not silently carry generic layer assumptions into a benchmark workflow:
use [graph-layers](../graph-layers/SKILL.md) for constructor-level semantics,
shape debugging, or unsupported convolution alternatives. See the four bundled
references for exact task flags, data layouts, checkpoints, reversible memory,
and failure diagnosis.

## Evidence boundary

Numbers printed in the README-derived tables are **documented benchmark
results**, tied to the repository's historical PyTorch/PyG environment and
external pretrained files. They are not results verified by this skill. The
bundled helper provides only a **verified tiny synthetic smoke** when it passes;
it does not validate OGB splits, ROC-AUC/accuracy/Hits, GPU memory, or training
quality. The selected inspection environment had PyTorch 2.11.0+cu128,
PyG 2.8.0.post1, matching scatter/cluster extensions, and OGB 1.3.6; DGL was
not selected. Modern PyG also has a known incompatibility in the repository's
SAGE wrapper; do not present that route as supported.
