# Training and Evaluation Troubleshooting

## Purpose

Use this reference when ModelScope training/evaluation setup fails before launch, during trainer construction, in hooks/checkpointing, or in distributed/GPU execution. Prefer safe preview and preflight before attempting a real job.

## Quick triage

1. Re-run the safe preview helper if the issue is about CLI flags or effective config:

   ```bash
   python scripts/build_training_args_preview.py --help
   ```

2. Confirm whether the failure happened during:
   - argument parsing/config preview,
   - model/dataset/config loading,
   - trainer construction,
   - `trainer.train()` loop,
   - `trainer.evaluate()` loop,
   - checkpoint load/save/upload,
   - distributed/AMP/GPU initialization.
3. Do not retry a real job until external prerequisites are explicit: model cache/network, dataset files, credentials, optional extras, GPU/VRAM, and work-dir policy.

## Common symptoms and recovery

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `unrecognized arguments` or a parser exits before preview | Flag name does not match base `TrainingArgs` or the recipe subclass; shell quoting split a value. | Check `references/training-args-reference.md`. Use underscores in base field names such as `--per_device_train_batch_size`. Quote flattened values and tuple-like values. |
| Flattened params do not appear under `train.optimizer` or `train.lr_scheduler` | Incorrect `key=value` syntax or comma-containing value. | Use `--optimizer_params weight_decay=0.01,eps=1e-8`. Validate with the preview helper before launch. |
| Defaults unexpectedly override a pretrained model config | `use_model_config`/`ignore_default_config` behavior misunderstood. | If fine-tuning a pretrained config, use `use_model_config=True` and merge only manual overrides in `cfg_modify_fn`. Preview both modes. |
| `Config file should not be None if model is not from pretrained!` | Default trainer was constructed with a model object or no model id and no `cfg_file`. | Supply `cfg_file`, pass a model id/local model directory with a config, or construct an appropriate task-specific trainer with required defaults. |
| `Detected plugins or allow_remote... trust_remote_code=True was not explicitly set` | The model configuration declares plugins/remote code and the builder refused unsafe execution. | Stop for trust review. Use a local trusted model, a model without remote code, or explicitly set `trust_remote_code=True` only when the user accepts the code-execution boundary. Route cache/download review to `../hub-and-cli/SKILL.md`. |
| Dataset column key errors such as missing `text`, `label`, `src_txt`, or preprocessor fields | Raw dataset columns do not match model/preprocessor expectations. | Inspect dataset columns safely, use `remap_columns`, add recipe subclass fields mapped to `preprocessor.*`, or use a `dataset_json_file` with `column_mapping`. Route detailed dataset checks to `../datasets-config/SKILL.md`. |
| `The train_dataset cannot be None.` or `The eval_dataset cannot be None.` | Real train/eval call lacks required dataset for the selected mode. | Supply datasets explicitly or configure `dataset.train`/`dataset.val` and split fields so the trainer can build them. |
| Metrics error when eval dataset exists | No configured metric and no task default metric was found. | Set `evaluation.metrics` or `--eval_metrics`; for best checkpointing, also set `metric_for_best_model` to an emitted metric key. |
| `Not find metric_key` during best checkpoint saving | `metric_for_best_model` does not match `trainer.metric_values`. | Run or inspect evaluation metric names, then set the exact key. Disable `save_best_checkpoint` until metric names are known. |
| `Trying to save the best checkpoint, but there is no evaluation` | Best-checkpoint hook configured without evaluation hook/cadence. | Configure `evaluation.period` with a positive interval and metrics, or disable best checkpoint saving. |
| Older checkpoints disappear | `max_checkpoint_num` or best-checkpoint retention limit is deleting old files by design. | Increase/disable retention before launch. Confirm the user accepts checkpoint deletion. |
| Unexpected Hub uploads or credential errors | `push_to_hub` or `push_to_hub_best` is enabled. | Disable push flags for local-only jobs. If upload is desired, require `repo_id`, token or `MODELSCOPE_API_TOKEN`, privacy/revision choice, and user authorization. |
| Optimizer or LR scheduler `KeyError` | Config names/options do not match installed torch/registered components. | Use common names (`AdamW`, `SGD`, `LinearLR`, `StepLR`) first, check optional dependencies, and ensure scheduler options match the chosen class. |
| `ReduceLROnPlateau` asks for `lr_scheduler_hook` | Plateau scheduler needs an explicit hook metric key. | Add `train.lr_scheduler_hook` with the required `metric_key` and strategy options, or choose a simpler scheduler. |
| `Please install swift by pip install ms-swift` | Efficient tuners were requested without the optional Swift package. | Install/verify `ms-swift` in the real training environment or remove `efficient_tuners`. |
| CUDA requested but unavailable or CPU torch installed | Domain model/trainer requires GPU but environment only has CPU backend. | Do not treat CPU import success as verification. Install a CUDA-compatible torch/domain stack and verify `torch.cuda.is_available()`, or narrow to CPU-supported models. |
| Out-of-memory during training/evaluation | Batch size, sequence/image resolution, model size, fp16/distributed config, or cache pressure exceeds available memory. | Lower batch size/sequence length/resolution, use gradient accumulation, verify mixed precision support, or choose a smaller model. Record that GPU execution is optional/unverified unless confirmed. |
| DDP/DeepSpeed/Megatron hangs or fails at init | Launch command/env vars/dependencies/process groups do not match hook config. | Use the correct launcher (`torchrun`, MPI, Slurm, or DeepSpeed as applicable), set rank/world-size variables, verify GPU count, install required packages, and test a tiny standalone distributed job before ModelScope training. |
| Checkpoint load mismatch or random-state warning | Loading a checkpoint saved by another processor/version or with partial state. | Decide whether `load_all_state=True` is required. For fine-tune/resume differences, use strict setting deliberately and document missing/unexpected keys. |
| Evaluation writes multiple partial prediction files | Distributed prediction-saving function writes per process. | Design a merge step after evaluation, or run single-process evaluation for prediction export. |

## Safe preview limitations

The bundled preview helper intentionally does not:

- import ModelScope,
- validate trainer names against the live registry,
- check that optimizer/LR scheduler names exist in torch,
- load model or dataset configs,
- resolve Hub credentials or cache,
- create `work_dir`,
- verify CUDA, DeepSpeed, Megatron, Apex, Swift, or domain extras,
- run `train()` or `evaluate()`.

If preview passes but a real job fails, use the phase-specific rows above and check external resources.

## Distributed and hook caveats

- `DDPHook` initializes distributed state and moves the model to `cuda:<local_rank>`. A working CPU import says nothing about DDP readiness.
- `DeepspeedHook` requires a DeepSpeed config path, DeepSpeed/transformers components, process launch, and compatible optimizer/checkpoint processors.
- `MegatronHook` depends on Megatron utilities and initialized model-parallel groups. It changes checkpoint file naming and save/load layout.
- AMP hooks require compatible torch CUDA AMP or Apex. Do not enable fp16 just because the config accepts the field.
- Hook priority controls execution order. Avoid mixing legacy hook entries with the newer nested config nodes for the same hook type; the default-config merge logic rejects duplicates for key hook families.

## When to stop and ask

Stop before launching or retrying when any of these are unknown:

- whether network/model downloads are allowed,
- whether remote code/plugins may execute,
- whether existing checkpoint/work-dir files may be overwritten or deleted,
- whether Hub uploads are allowed and which credentials/repository to use,
- whether a GPU-only model may be replaced with a CPU-friendly model,
- whether a partial backend verification is acceptable.

This production scope classified broad CUDA/domain training as optional and unverified. A later Researcher can run a targeted backend verification only after the user supplies the concrete model, data, extras, and hardware constraints.
