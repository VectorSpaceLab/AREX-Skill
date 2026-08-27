# PocketFlow Learner Catalog

Read this to choose the exact `--learner` value and the main hyperparameter family.

## Verified learner id mapping

`create_learner(sm_writer, model_helper)` maps `FLAGS.learner` to these classes:

| Learner id | Class | Use for | Notes |
| --- | --- | --- | --- |
| `full-prec` | `FullPrecLearner` | Baseline training/evaluation without compression. | Also supplies teacher/original model behavior for distillation-oriented workflows. |
| `channel` | `ChannelPrunedLearner` | LASSO/linear-regression channel pruning with uniform, list, or RL-selected preserve ratios. | Older channel-pruning path; supports group fine-tuning and distillation. |
| `chn-pruned-rmt` | `ChannelPrunedRmtLearner` | Remastered channel pruning with ISTA/lstsq reconstruction. | Simpler implementation; RL support is not ready in docs. |
| `chn-pruned-gpu` | `ChannelPrunedGpuLearner` | GPU-oriented channel pruning implementation. | More hardware-specific; verify source and environment before using. |
| `dis-chn-pruned` | `DisChnPrunedLearner` | Discrimination-aware channel pruning (DCP). | Needs staged block/layer fine-tuning and often pretrained warm-start. |
| `weight-sparse` | `WeightSparseLearner` | Dynamic weight sparsification / pruning masks. | Can use uniform, heuristic, or RL-optimized pruning ratios. |
| `uniform` | `UniformQuantLearner` | Self-developed uniform quantization with bucketing and optional RL bit allocation. | Compresses weights/activations; acceleration depends on downstream runtime. |
| `uniform-tf` | `UniformQuantTFLearner` | TensorFlow quantization-aware training wrapper. | Designed for 8-bit-ish TF quantization and TFLite export. |
| `non-uniform` | `NonUniformQuantLearner` | Non-uniform quantization with optimizable clusters. | Compression-oriented; not directly accelerated by ordinary low-precision kernels. |

Invalid values raise `ValueError: unrecognized learner's name`.

## Cross-cutting learner flags

| Flag | Meaning |
| --- | --- |
| `--learner` | Selects one of the ids above. |
| `--exec_mode train|eval` | Run training or download/evaluate a model. |
| `--enbl_dst` | Enables distillation loss where supported. |
| `--enbl_warm_start` | Enables warm-start behavior where a helper/learner supports it. |
| `--save_path`, `--save_path_eval` | General checkpoint paths; individual learners often override with learner-specific paths. |
| `--model_http_url` | Base URL for pretrained model archive downloads. |

## Channel pruning flags

### `channel`

Important flags include:

- `cp_prune_option`: `uniform`, `list`, or `auto`.
- `cp_uniform_preserve_ratio`: preserve ratio for uniform pruning.
- `cp_preserve_ratio`: target global preserve ratio for RL/auto pruning.
- `cp_prune_list_file`: comma-separated layer ratio list for list mode.
- `cp_nb_rlouts`, `cp_nb_rlouts_min`: RL rollout controls.
- `cp_finetune`, `cp_retrain`, `cp_list_group`, `cp_nb_iters_ft_ratio`, `cp_lrn_rate_ft`: group fine-tuning/retraining controls.
- `cp_nb_points_per_layer`, `cp_nb_batches`, `cp_quadruple`: channel selection/reconstruction controls.

### `chn-pruned-rmt`

Important flags include:

- `cpr_prune_ratio`: target input-channel pruning ratio.
- `cpr_skip_frst_layer`, `cpr_skip_last_layer`, `cpr_skip_op_names`: skip sensitive Conv2D operations.
- `cpr_nb_smpls`, `cpr_nb_crops_per_smpl`: cached sample controls.
- `cpr_ista_lrn_rate`, `cpr_ista_nb_iters`: ISTA pruning solve.
- `cpr_lstsq_lrn_rate`, `cpr_lstsq_nb_iters`: least-square reconstruction.
- `cpr_warm_start`, `cpr_save_path_ws`: warm-start from a previously pruned model.

### `dis-chn-pruned`

Important flags include:

- `dcp_prune_ratio`: target pruning ratio.
- `dcp_nb_stages`: number of channel pruning stages.
- `dcp_lrn_rate_adam`, `dcp_nb_iters_block`, `dcp_nb_iters_layer`: staged fine-tuning controls.
- `dcp_save_path`, `dcp_save_path_eval`: DCP checkpoint outputs.

## Weight sparsification flags

Important `weight-sparse` flags include:

- `ws_prune_ratio`: target sparsity/pruning ratio.
- `ws_prune_ratio_prtl`: `uniform`, `heurist`, or `optimal`.
- `ws_reward_type`: `single-obj` or `multi-obj` for RL reward.
- `ws_nb_rlouts`, `ws_nb_rlouts_min`: RL rollout controls.
- `ws_lrn_rate_rg`, `ws_nb_iters_rg`: layer-wise regression.
- `ws_lrn_rate_ft`, `ws_nb_iters_ft`: global fine-tuning.
- `ws_nb_iters_feval`: fast-evaluation iterations.
- `ws_prune_ratio_exp`, `ws_iter_ratio_beg`, `ws_iter_ratio_end`, `ws_mask_update_step`: dynamic pruning schedule.

## Quantization flags

### `uniform`

- `uql_weight_bits`, `uql_activation_bits`: quantization bit widths.
- `uql_use_buckets`, `uql_bucket_type`, `uql_bucket_size`: bucketing.
- `uql_quantize_all_layers`: include first/last layers.
- `uql_quant_epochs`: quantization fine-tuning epochs.
- `uql_enbl_rl_agent`: enable RL bit allocation.
- `uql_equivalent_bits`, `uql_w_bit_min`, `uql_w_bit_max`, `uql_nb_rlouts`: RL bit-budget controls.

### `uniform-tf`

- `uqtf_weight_bits`, `uqtf_activation_bits`: TF quantization bit widths.
- `uqtf_quant_delay`: step delay before quantization.
- `uqtf_freeze_bn_delay`: batch-norm moving-stat freeze delay.
- `uqtf_lrn_rate_dcy`: learning-rate decay for quantized model.
- `uqtf_enbl_manual_quant`: manual quantization path where supported.

### `non-uniform`

- `nuql_opt_mode`: `weights`, `clusters`, or `both`.
- `nuql_init_style`: `quantile` or `uniform` cluster initialization.
- `nuql_weight_bits`, `nuql_activation_bits`: quantization bit widths.
- `nuql_use_buckets`, `nuql_bucket_type`, `nuql_bucket_size`: bucketing.
- `nuql_enbl_rl_agent` and `nuql_*` RL controls mirror the uniform quantization prefix.

## Distillation flags

- `--enbl_dst` turns on distillation loss.
- `loss_w_dst` controls distillation loss weight.
- `tempr_dst` controls softmax temperature.
- `save_path_dst` points at teacher/original model checkpoints.

Only enable distillation when the original/teacher checkpoint is available and compatible with the selected model helper.
