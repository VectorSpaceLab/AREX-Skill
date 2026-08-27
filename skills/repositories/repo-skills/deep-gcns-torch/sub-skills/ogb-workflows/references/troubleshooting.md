# OGB troubleshooting and boundaries

## No downloads or long runs

`PygNodePropPredDataset`, `PygGraphPropPredDataset`, and
`PygLinkPropPredDataset` may download when their processed data is absent.
The protein dataset helper can also create feature and edge-index cache files
in the current working directory. Check for an approved, already-cached data
root before constructing a dataset. Do not use the bundled smoke to test data
availability: it intentionally never imports a dataset constructor or performs
network I/O. External pretrained files mentioned by the task READMEs are not
included.

If the user needs a real run, ask for dataset/cache readiness, an explicit
output directory, hardware, and a bounded epoch/evaluation budget. Do not
silently turn a CPU smoke into a 28-, 112-, 448-, or 1001-layer training run.

## Backend and API drift

- Verify `torch`, `torch_geometric`, `torch_scatter`, and `torch_cluster` are
  importable and mutually compatible. Compiled extension failures usually mean
  the PyTorch/PyG wheel family is mismatched; repair the environment rather
  than changing model flags.
- The repository targets an older PyG API. Its `sage`/`rsage` wrapper fails
  against modern PyG because it expects an older `SAGEConv` weight contract and
  type inspection behavior. Prefer the verified GENConv route; do not call
  SAGE a supported fallback.
- DGL RevGAT is not a PyG fallback. It needs DGL CUDA, the DGL OGB adapter, and
  DGL graph operations. If DGL is absent, record `SKIP_NOT_SELECTED`, not a
  model failure or a successful result.
- `--block dense` is accepted or mentioned by some parsers but the OGB model
  implementations raise `NotImplementedError`. Use `plain`, `res`, or `res+`.
- Task parser aggregator choices differ. `softmax_sum` and `power_sum` appear
  in some historical help/docs, while the inspected live GENConv smoke covered
  `max`, `mean`, `add`, `softmax`, `softmax_sg`, and `power`. Run task
  `--help` and inspect the installed constructor before selecting an uncommon
  option.

## Shape, feature, and memory failures

- **Molecular encoder error:** `AtomEncoder`/`BondEncoder` require integer OGB
  categorical columns with the expected feature count. `--feature simple`
  intentionally slices to two columns. Do not feed arbitrary float widths.
- **Edge encoding mismatch:** `--conv_encode_edge` changes whether the model
  passes raw edge attributes into GENConv's bond-aware path. In protein models,
  edge embeddings are width `hidden_channels`; in reversible models they are
  repeated and chunked by `group`.
- **Virtual node error:** `--add_virtual_node` requires a graph `batch` vector
  and graph count derived from it. It is a molecular option, not a node-task
  switch.
- **Partitioned node task is unexpectedly inaccurate:** induced subgraphs drop
  cross-partition edges by design. Confirm cluster count, seed, train/eval
  partition policy, and node index remapping before changing the model.
- **Reversible construction fails:** require `hidden_channels % group == 0`,
  a feature file with the expected node width, edge attributes of width 8,
  and edge embeddings whose last dimension is divisible by `group`. Keep
  `--group 2` unless a deliberate wider grouping is tested.
- **OOM:** reduce graph partition size/count policy, hidden width, layer count,
  batch size, or evaluation views; use the reversible path only with its exact
  shape contract. A tiny CPU forward says nothing about large-graph GPU
  memory. Do not claim the documented 32/48 GB recommendations were verified.
- **CUDA-only call on CPU:** the efficient proteins main path reports CUDA peak
  memory and uses CUDA AMP utilities; use the regular non-reversible CPU model
  for API smoke, not the full efficient training script.

## Checkpoint and evaluation failures

- Standard OGB checkpoints contain `model_state_dict`; the link task has a
  second predictor checkpoint. If loading reports missing/unexpected keys,
  compare all architecture and feature flags before using `strict=False`.
- CPU load should use `torch.load(..., map_location="cpu")`; loading a GPU
  checkpoint without mapping can fail on a CPU-only host.
- Arxiv and products node models return log-softmax class scores and evaluate
  with argmax accuracy. Proteins returns logits and evaluates multi-label
  ROC-AUC. Molecular tasks use dataset-specific masked labels/metrics. PPA
  evaluates class accuracy. Collab evaluates Hits@K. Do not compare these
  metrics as if they were interchangeable.
- A checkpoint filename is not evidence of a reported number. Historical
  README numbers depend on data version, flags, repeated runs, and external
  pretrained assets; label them documented, not smoke-verified.

## Working-directory imports

The native task files use imports such as `import __init__`, `from args import
ArgsInit`, and `from model import DeeperGCN`. They are intended to run from the
corresponding task directory with the repository root available on `sys.path`.
They are not portable package imports. For arbitrary-cwd validation use only
`scripts/ogb_model_smoke.py`, which contains no checkout-relative import and no
source-repository link.

## Routing

Use **graph-layers** for GENConv constructor signatures, aggregation formulas,
PyG extension diagnostics, and primitive reversible APIs. Use
**ppi-workflows** for PPI's data and F1 conventions. Use
**point-cloud-workflows** for ModelNet/S3DIS/PartNet layouts and dense point
shapes.
