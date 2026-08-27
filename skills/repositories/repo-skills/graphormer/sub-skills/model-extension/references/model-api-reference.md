# Graphormer model API reference

This reference is for agents extending a Graphormer fairseq user-dir. It is self-contained and summarizes verified registry names, signatures, defaults, import behavior, and model/criterion output contracts.

## Fairseq user-dir import behavior

Graphormer is used as a fairseq user-dir plugin. Pass the directory that contains Graphormer's `models/`, `tasks/`, and `criterions/` packages as `--user-dir`, or call `fairseq.utils.import_user_module(argparse.Namespace(user_dir=<graphormer-package-dir>))` before reading fairseq registries.

Relevant import behavior:

- `import_user_module` resolves `args.user_dir`, imports the top-level module once per process, and memoizes the exact module path.
- The top-level Graphormer module imports `graphormer.criterions`; that package imports every non-private Python file in `criterions/`.
- fairseq then imports every non-private Python file or package in `tasks/` and `models/`.
- Registration decorators execute at import time. A model, task, criterion, or architecture is invisible until the file defining its decorator has been imported.
- The directory basename becomes the Python module name. If that module name is already present in `sys.modules`, fairseq raises a duplicate-name import error instead of silently shadowing it.
- A fresh Python process is the most reliable way to re-check registries after editing registration files, because memoization and module caching can keep old imports alive.

## Verified Graphormer registry names

| Registry | Names | Notes |
| --- | --- | --- |
| Models | `graphormer`, `graphormer3d` | `graphormer` is the graph-level encoder model; `graphormer3d` is the OC20/IS2RE 3D model. |
| Architectures | `graphormer`, `graphormer_base`, `graphormer_slim`, `graphormer_large`, `graphormer3d_base` | Use these values with `--arch` after importing the user-dir. |
| Tasks | `graph_prediction`, `graph_prediction_with_flag`, `is2re` | `graph_prediction_with_flag` adds FLAG perturbation training behavior; `is2re` is the Graphormer3D/OC20 task. |
| Criterions | `l1_loss`, `binary_logloss`, `multiclass_cross_entropy`, `l1_loss_with_flag`, `binary_logloss_with_flag`, `multiclass_cross_entropy_with_flag`, `mae_deltapos` | Graph-level criterions slice graph-token logits; `mae_deltapos` consumes Graphormer3D energy and node-displacement outputs. |

## Installed-fact signatures

| Object | Signature | Operational meaning |
| --- | --- | --- |
| `GraphormerModel.forward` | `(self, batched_data, **kwargs)` | Passes `batched_data` plus optional kwargs to `GraphormerEncoder`. |
| `GraphormerModel.build_model` | `(args, task)` | Applies architecture defaults, ensures `max_nodes`, builds `GraphormerEncoder`. |
| `GraphormerEncoder.forward` | `(self, batched_data, perturb=None, masked_tokens=None, **unused)` | Accepts batched graph dicts and optional FLAG perturbation. `masked_tokens` is not implemented. |
| `Graphormer3D.forward` | `(self, atoms: torch.Tensor, tags: torch.Tensor, pos: torch.Tensor, real_mask: torch.Tensor)` | Accepts padded 3D atom tensors and returns energy, node displacement, and node target mask. |
| `GraphormerDataset.__init__` | `(self, dataset: Optional[PyG-or-DGL-dataset] = None, dataset_spec: Optional[str] = None, dataset_source: Optional[str] = None, seed: int = 0, train_idx=None, valid_idx=None, test_idx=None)` | Dataset contract is owned by the dataset sub-skill; model/task authors only need the resulting `batched_data` or 3D tensors. |
| `BatchedDataDataset.__init__` | `(self, dataset, max_node=128, multi_hop_max_dist=5, spatial_pos_max=1024)` | Collates graph prediction examples into the `batched_data` dict consumed by `GraphormerModel`. |
| `register_dataset` | `(name: str)` | Custom dataset registration is routed to the dataset sub-skill. |
| `preprocess_item` | `(item)` | Produces graph fields consumed by the Graphormer encoder. |

## Graph prediction config defaults

`graph_prediction` and `graph_prediction_with_flag` share these task defaults unless overridden:

| Field | Default |
| --- | --- |
| `dataset_name` | `pcqm4m` |
| `num_classes` | `-1` |
| `max_nodes` | `128` |
| `dataset_source` | `pyg` |
| `num_atoms` | `4608` |
| `num_edges` | `1536` |
| `num_in_degree` | `512` |
| `num_out_degree` | `512` |
| `num_spatial` | `512` |
| `num_edge_dis` | `128` |
| `multi_hop_max_dist` | `5` |
| `spatial_pos_max` | `1024` |
| `edge_type` | `multi_hop` |
| `pretrained_model_name` | `none` |
| `load_pretrained_model_output_layer` | `False` |
| `train_epoch_shuffle` | `False` |
| `user_data_dir` | empty string |

`graph_prediction_with_flag` adds:

| Field | Default |
| --- | --- |
| `flag_m` | `3` |
| `flag_step_size` | `0.001` |
| `flag_mag` | `0.001` |

Important: `GraphPredictionTask.setup_task` asserts `num_classes > 0`. Do not rely on the `-1` default for a real graph prediction run.

## Architecture defaults

### `graphormer`

The base `graphormer` architecture fills these defaults:

| Parameter | Default |
| --- | --- |
| `dropout` | `0.1` |
| `attention_dropout` | `0.1` |
| `act_dropout` | `0.0` |
| `encoder_ffn_embed_dim` | `4096` |
| `encoder_layers` | `6` |
| `encoder_attention_heads` | `8` |
| `encoder_embed_dim` | `1024` |
| `share_encoder_input_output_embed` | `False` |
| `no_token_positional_embeddings` | `False` |
| `apply_graphormer_init` | `False` |
| `activation_fn` | `gelu` |
| `encoder_normalize_before` | `True` |

### `graphormer_base`

`graphormer_base` sets `encoder_embed_dim=768`, `encoder_layers=12`, `encoder_attention_heads=32`, `encoder_ffn_embed_dim=768`, `dropout=0.0`, `attention_dropout=0.1`, `act_dropout=0.1`, `activation_fn=gelu`, `encoder_normalize_before=True`, `apply_graphormer_init=True`, `share_encoder_input_output_embed=False`, `no_token_positional_embeddings=False`, and `pre_layernorm=False`, then delegates remaining missing fields to `graphormer` defaults. The pretrained-name branch forces the same core dimensions for the known base pretrained models.

### `graphormer_slim`

`graphormer_slim` sets `encoder_embed_dim=80`, `encoder_layers=12`, `encoder_attention_heads=8`, `encoder_ffn_embed_dim=80`, `activation_fn=gelu`, `encoder_normalize_before=True`, `apply_graphormer_init=True`, `share_encoder_input_output_embed=False`, `no_token_positional_embeddings=False`, and `pre_layernorm=False`, then delegates remaining missing fields to `graphormer` defaults.

### `graphormer_large`

`graphormer_large` sets `encoder_embed_dim=1024`, `encoder_layers=24`, `encoder_attention_heads=32`, `encoder_ffn_embed_dim=1024`, `activation_fn=gelu`, `encoder_normalize_before=True`, `apply_graphormer_init=True`, `share_encoder_input_output_embed=False`, `no_token_positional_embeddings=False`, and `pre_layernorm=False`, then delegates remaining missing fields to `graphormer` defaults.

### `graphormer3d_base`

`graphormer3d_base` sets `blocks=4`, `layers=12`, `embed_dim=768`, `ffn_embed_dim=768`, `attention_heads=48`, `input_dropout=0.0`, `dropout=0.1`, `attention_dropout=0.1`, `activation_dropout=0.0`, `node_loss_weight=15`, `min_node_loss_weight=1`, `eng_loss_weight=1`, and `num_kernel=128`.

## Model output and head notes

### Graph-level `graphormer`

`GraphormerModel.forward(batched_data, **kwargs)` returns the tensor produced by `GraphormerEncoder.forward`. Internally the graph encoder prepends a graph token, so outputs are shaped like batch by tokens by channels. Graph-level criterions use `logits[:, 0, :]` as the graph representation/output.

The normal output head is `embed_out: Linear(encoder_embed_dim, num_classes)` plus a learned scalar bias. Therefore:

- For regression with `l1_loss`, set `num_classes` to the number of regression targets, usually `1` for scalar graph regression.
- For binary classification with `binary_logloss`, set `num_classes=1`; targets may contain NaNs, which the criterion masks.
- For multiclass classification with `multiclass_cross_entropy`, set `num_classes` to the number of classes; targets are class indices.
- `share_encoder_input_output_embed=True` is not implemented in this Graphormer model path.
- If a transfer or fine-tuning path removes or skips the output head, check the resulting channel count before using graph-level criterions.
- `load_pretrained_model_output_layer=False` resets the final output layer after loading known pretrained base checkpoints; set it only when the pretrained output head is intentionally compatible.

`GraphormerGraphEncoder.forward` returns `(inner_states, graph_rep)`, where `graph_rep` is the graph token hidden state before the task output projection. Custom models can use `GraphormerGraphEncoder` or the lower-level `GraphNodeFeature`/`GraphAttnBias` modules, but should make their final output shape explicit.

### FLAG compatibility

`graph_prediction_with_flag` creates a perturbation tensor with shape `(batch, nodes, model.encoder_embed_dim)` and stores it in `sample["perturb"]`. FLAG-compatible models must accept `perturb=` and add it to node representations, as `GraphormerEncoder.forward` does. If a custom model omits perturb support, route users to the non-FLAG task and criterion names.

### Graphormer3D

`Graphormer3D.forward(atoms, tags, pos, real_mask)` expects:

- `atoms`: integer tensor shaped `(batch, nodes)` with `0` used for padding.
- `tags`: integer tensor shaped `(batch, nodes)` with values compatible with a size-3 tag embedding.
- `pos`: floating tensor shaped `(batch, nodes, 3)`.
- `real_mask`: boolean-like tensor shaped `(batch, nodes)` marking real atoms for node loss.

It returns `(eng_output, node_output, node_target_mask)`:

- `eng_output`: scalar energy prediction per graph, shaped `(batch,)` after aggregation.
- `node_output`: per-node vector prediction, shaped `(batch, nodes, 3)`.
- `node_target_mask`: mask shaped `(batch, nodes, 1)` used by `mae_deltapos`.

`mae_deltapos` expects the sample to provide `targets.relaxed_energy` and `targets.deltapos`, and combines normalized energy MAE with node displacement MAE using the model's update count and node-loss weights.
