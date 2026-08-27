# CLI parameters

This reference collects the Graphormer-specific `fairseq-train` flags that are
most likely to matter when building or reviewing a training command.

## Model and architecture flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--arch` | Selects the registered Graphormer architecture | Common values: `graphormer_slim`, `graphormer_base`, `graphormer_large`, `graphormer3d_base`. |
| `--encoder-layers` | Number of encoder layers | Graphormer base and slim recipes both override this. |
| `--encoder-embed-dim` | Hidden size | 80 for ZINC slim, 768 for base recipes, 1024 for large. |
| `--encoder-ffn-embed-dim` | Feed-forward width | Usually matches the hidden size in the documented recipes. |
| `--encoder-attention-heads` | Attention head count | 8 for slim, 32 for base, 48 for Graphormer3D. |
| `--apply-graphormer-init` | Use Graphormer-specific initialization | Architecture defaults usually set this for the base/slim/large family. |
| `--pre-layernorm` | Use pre-layernorm behavior where supported | Important for MolHIV fine-tuning and some pretrained paths. |

## Training and optimization flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--task` | Selects the fairseq task | Graph prediction uses `graph_prediction` or `graph_prediction_with_flag`; OC20/IS2RE uses `is2re`. |
| `--criterion` | Selects the loss | Match the task: `l1_loss`, `binary_logloss`, `multiclass_cross_entropy`, `*_with_flag`, or `mae_deltapos`. |
| `--optimizer` | Optimizer choice | Documented recipes use `adam`. |
| `--lr-scheduler` | Learning-rate schedule | Documented recipes use `polynomial_decay`. |
| `--lr` | Base learning rate | 2e-4 in the common property-prediction recipes. |
| `--warmup-updates` | Warmup steps | Often 60000 for graph prediction and 10000 for OC20/IS2RE. |
| `--total-num-update` | Total update budget | Large in the property-prediction and OC20 recipes. |
| `--batch-size` | Batch size | Must match memory and task constraints; OC20 uses a very small batch. |
| `--fp16` | Mixed precision | Common in the historical CUDA recipes. |
| `--clip-norm` | Gradient clipping | Commonly 5.0. |
| `--weight-decay` | Weight decay | 0.01 for ZINC, 0.0 for many base recipes, 0.001 for OC20. |
| `--data-buffer-size` | Prefetch buffer size | 20 in most documented recipes. |
| `--num-workers` | Data-loader workers | 16 for property tasks, 0 for the OC20 LMDB example. |
| `--save-dir` | Checkpoint output directory | Keep this directory checkpoint-only when you plan checkpoint evaluation later. |
| `--seed` | Random seed | Usually 1 in the documented examples. |

## Dataset and data-layout flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--dataset-source` | Built-in dataset source | Graphormer accepts `pyg`, `dgl`, and `ogb` for built-in dataset lookup. |
| `--dataset-name` | Built-in dataset name | Examples include `zinc`, `pcqm4m`, `pcqm4mv2`, `ogbg-molhiv`. |
| `--num-classes` | Target dimensionality | Required to be positive for `graph_prediction`; usually `1` for regression and binary classification. |
| `--user-data-dir` | Custom dataset module directory | Do not combine with built-in dataset-source selection for the same workflow. |
| `--multi-hop-max-dist` | Maximum multi-hop edge history | Shared with the batch wrapper. |
| `--spatial-pos-max` | Distance mask threshold | Shared with the batch wrapper. |
| `--max-nodes` | Per-graph node cap | Graphs larger than this are dropped during batching. |
| `--num-atoms`, `--num-edges`, `--num-in-degree`, `--num-out-degree`, `--num-spatial`, `--num-edge-dis` | Feature vocabulary sizes | Defaults are the historical Graphormer values from the task config. |
| `--edge-type` | Edge encoding style | Default is `multi_hop`. |

## Pretrained and FLAG-specific flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--pretrained-model-name` | Pretrained checkpoint family | Examples include `pcqm4mv1_graphormer_base`, `pcqm4mv2_graphormer_base`, and the MolHIV-oriented checkpoint. |
| `--load-pretrained-model-output-layer` | Keep the pretrained output layer | Use only when the source head matches the target task. |
| `--flag-m` | FLAG iteration count | Used by `graph_prediction_with_flag`. |
| `--flag-step-size` | FLAG step size | Used by `graph_prediction_with_flag`. |
| `--flag-mag` | FLAG perturbation bound | Used by `graph_prediction_with_flag`. |

## Practical reminders

- `num_classes` is not optional for real graph prediction runs.
- The training recipe should match the dataset and metric family.
- Use the root environment checker if you only need to confirm that the Graphormer registries are visible before composing a command.
