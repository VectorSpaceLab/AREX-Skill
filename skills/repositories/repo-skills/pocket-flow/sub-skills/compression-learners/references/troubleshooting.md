# Compression Learner Troubleshooting

Use this reference after a learner command has been assembled but before starting expensive training, or when a PocketFlow learner fails early. For launcher setup, `path.conf`, TensorFlow import, GPU discovery, Docker, Seven, Horovod, or TF-Plus checks, route to [execution-config](../../execution-config/SKILL.md).

## Fast triage

1. Validate the learner id against [learner-catalog.md](learner-catalog.md).
2. Preview the command with [`../scripts/build_learner_command.py`](../scripts/build_learner_command.py) before running any official launcher.
3. Confirm the active run script defines the model/dataset flags used in the command; custom run-script and `ModelHelper` issues belong to [custom-models-data](../../custom-models-data/SKILL.md).
4. Confirm data directories and pretrained checkpoints exist or that a deliberate bounded download policy is in place.
5. Treat full native training, performance recovery, RL search, Docker/Seven jobs, and multi-GPU runs as long-running and not verified by this skill.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: unrecognized learner's name` | Learner id typo or unsupported alias. | Use exactly one of `full-prec`, `weight-sparse`, `channel`, `chn-pruned-gpu`, `chn-pruned-rmt`, `dis-chn-pruned`, `uniform`, `uniform-tf`, `non-uniform`. The flag is `--learner`, not `--learners`. |
| TensorFlow reports an unknown flag such as `uql_quant_epoch` or `nuql_quant_epoch` | Some docs use singular names, but source code defines plural names. | Use `--uql_quant_epochs` and `--nuql_quant_epochs`. |
| TensorFlow reports unknown flag `ws_update_mask_step` | AutoML/source bridge naming mismatch; learner source defines `ws_mask_update_step`. | Normalize to `--ws_mask_update_step` before running a learner. |
| `tf.contrib` or `tensorflow.contrib.lite/quantize` missing | TensorFlow 2.x or an incompatible TensorFlow 1.x package is active. | Use a Python 3.6-era TensorFlow 1.x environment. `uniform-tf` specifically needs `tf.contrib.quantize`; deployment/conversion may need `tf.contrib.lite`. |
| Learner tries to download a model or says local model files do not exist | Compression learner called `download_model()` and no checkpoint was present at the expected save path. | Provide a full-precision/pretrained checkpoint, set the relevant `--save_path`/learner `*_save_path*`, or configure `--model_http_url` only if network downloads are approved. |
| Training command hangs or takes far longer than expected | Full training, RL roll-outs, DCP stages, channel selection, or quantization fine-tuning are expensive. | Reduce rollout/stage/iteration counts only for smoke experiments; do not claim final performance from reduced settings. |
| `nvidia-smi` missing or no idle GPU found | Official local launcher expects NVIDIA GPU discovery. | Use `execution-config` runtime checks. For CPU-only static previews, use this sub-skill's helper and avoid running official launchers. |
| Horovod/TF-Plus warning appears | Optional multi-GPU backends are absent. | Single-GPU/CPU command construction can still be valid; multi-GPU execution needs the optional backend and belongs to `execution-config`. |
| Compression runs but accuracy collapses | Pruning/quantization ratio too aggressive, insufficient fine-tuning, bad pretrained checkpoint, data mismatch, or distillation teacher mismatch. | Back off pruning ratio/bit-width, enable or tune distillation, increase fine-tuning/rollout/stage counts, and verify data/checkpoint/model pairing. |
| TFLite export differs between `uniform` and `uniform-tf` | These are different learners. | Use `uniform-tf` for TensorFlow QAT/TFLite-oriented workflows, then route export to [deployment-conversion](../../deployment-conversion/SKILL.md). The self-developed `uniform` learner has its own quantized checkpoint path and is not the same export flow. |

## Learner-specific checks

### Full precision

- Confirm whether the task is `train` or `eval`. Direct mode needs `--exec_mode train|eval`.
- Use `full-prec` as the baseline before evaluating compressed accuracy.
- If `--enbl_dst` is enabled on a baseline, verify that teacher checkpoint paths do not overwrite baseline output paths.

### Original channel pruning: `channel`

- `--cp_prune_option` must be `uniform`, `list`, or `auto`.
- For `uniform`, use `--cp_uniform_preserve_ratio` and remember it is per-layer; total FLOPs preservation may be lower than the per-layer value for sequential convolutions and different around residual connections.
- For `list`, ensure the ratio file has the expected number/order of convolution-layer values.
- For `auto`, expect DDPG cost. Check `--cp_nb_rlouts`, `--cp_nb_rlouts_min`, and `--cp_reward_policy` before launching.
- `--cp_finetune`, `--cp_retrain`, and `--cp_list_group` change group tuning behavior and runtime.

### Remastered channel pruning: `chn-pruned-rmt`

- Do not promise RL auto tuning; official documentation says it is not ready for this learner.
- If `--cpr_warm_start=True`, verify `--cpr_save_path_ws` points to a valid channel-pruned checkpoint prefix.
- Use `--cpr_skip_frst_layer`, `--cpr_skip_last_layer`, or `--cpr_skip_op_names` for fragile input/output or residual-block convolutions.
- Large `--cpr_nb_smpls` and `--cpr_nb_crops_per_smpl` can improve channel selection but increase memory/runtime.

### GPU-based channel pruning: `chn-pruned-gpu`

- Use only with `cpg_*` flags; do not mix with `cp_*` or `cpr_*` flags unless a run script deliberately defines them for another purpose.
- `--cpg_prune_ratio_type` must be `uniform` or `list`; `list` requires `--cpg_prune_ratio_file`.
- The implementation is code-evidenced but less documented publicly; validate on a small bounded case before a costly run.

### Discrimination-aware channel pruning: `dis-chn-pruned`

- Requires a pretrained full model and enough data for block-wise and layer-wise fine-tuning.
- More `--dcp_nb_stages` can improve stage granularity but increases runtime.
- `--dcp_lrn_rate_adam` too high can destabilize block/layer fine-tuning; too low can stall recovery.

### Weight sparsification

- `--ws_prune_ratio_prtl` must be `uniform`, `heurist`, or `optimal`.
- `optimal` invokes RL and needs a pretrained model; for a cheap baseline, use `uniform` first.
- Keep `0 <= --ws_prune_ratio < 1` for practical runs. Extreme sparsity can collapse accuracy or produce all-zero layers.
- Make sure `--ws_iter_ratio_beg < --ws_iter_ratio_end`; masks update only at `--ws_mask_update_step` intervals.

### Uniform quantization

- Use `--uql_weight_bits` and `--uql_activation_bits`; low bits can cause severe accuracy loss without enough fine-tuning.
- `--uql_use_buckets=True` with `--uql_bucket_type channel` is usually cheaper than `split`; smaller split buckets increase overhead.
- `--uql_quantize_all_layers=False` leaves first/last layers unquantized for accuracy; set it only when the deployment target requires all layers quantized.
- `--uql_enbl_rl_agent=True` triggers long DDPG search; check `uql_equivalent_bits`, bit min/max, and tuning steps.

### TensorFlow QAT: `uniform-tf`

- Requires TF1 quantization APIs. TensorFlow 2 or stripped TF1 builds will fail early.
- `--uqtf_weight_bits` and `--uqtf_activation_bits` are documented around 8-bit use. Non-8-bit settings may not translate to the expected mobile deployment flow.
- `--uqtf_quant_delay` delays quantization; `--uqtf_freeze_bn_delay` affects batch-norm moving statistics.
- Use `deployment-conversion` after checkpoint creation for `.pb`/`.tflite` export and post-quantization options.

### Non-uniform quantization

- `--nuql_opt_mode` must be `weights`, `clusters`, or `both`.
- `--nuql_init_style` must be `quantile` or `uniform`.
- Non-uniform quantization does not provide direct integer-arithmetic acceleration in common runtimes; route deployment expectations carefully.
- RL flags mirror `uql_` names with `nuql_` prefixes and have the same cost cautions.

## When not to run

Do not launch official training/performance commands when any of these are unresolved:

- TensorFlow 1.x APIs are unavailable.
- Required dataset paths or pretrained checkpoints are unknown.
- The command is a Seven/Docker/multi-GPU command and the matching infrastructure is not approved.
- The task only asks for planning, command preview, or troubleshooting; use the bundled helper instead.
