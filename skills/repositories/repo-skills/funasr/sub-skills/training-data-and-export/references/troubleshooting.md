# Training, data, and export troubleshooting

Use this reference before mutating data or rerunning long jobs. Prefer tiny manifest fixtures, CLI help, and static config checks before training/export.

## Manifest failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `validate_manifest.py` reports missing `source`, `target`, or `key`. | A JSONL line is not the standard audio schema, or a conversion silently dropped a field. | Fix the line or choose `--schema messages` only for conversational LLM-ASR data. Standard ASR training needs `key`, `source`, and `target`. |
| Duplicate key errors. | Two utterances share an id in `wav.scp`, text, or JSONL. | Rename one id and regenerate. Do not let later lines overwrite earlier lines. |
| `target_len` mismatch. | `target_len` was hand-edited or computed with a different word/character rule. | Recompute: use word count when the target contains spaces, otherwise character count. Regenerate with `make_jsonl_from_scp.py` if possible. |
| `source_len` mismatch. | Duration changed, source path points to a different file, or a placeholder length was used. | Recompute from the actual local WAV. For URI sources, run a loader smoke or use a trusted precomputed duration. |
| Missing local audio path. | `wav.scp` references a file that is not present from the current training environment. | Fix the path, mount/copy data, or intentionally use a URI that the loader can access. Validate again with `--check-sources`. |
| Converted JSONL is unexpectedly empty. | The public converter skips missing local `source` entries; URI strings and nonexistent files can be skipped depending on the converter path. | Use the bundled converter in strict mode to fail early, or disable source checks only when URI loading is intentional. |

## `wav.scp` and text mismatch

`wav.scp` and text files should have the same key set. If line counts differ or ids are misaligned:

1. Sort or join by key; do not rely on line position.
2. Fail on keys that are only present in one file unless the user explicitly asks to keep the intersection.
3. Regenerate JSONL.
4. Validate duplicate keys and length fields.

## Large-data memory issues

Symptoms: dataloader memory growth, very slow startup, or out-of-memory before the first useful training step.

Recoveries:

- Split training JSONL into shards and pass a shard-list file to `train_data_set_list`.
- Set `++dataset_conf.data_split_num` to the intended number of sequential groups.
- Reduce `dataset_conf.batch_size`, switch from `example` to `token` batching when appropriate, or reduce `num_workers`.
- Balance heterogeneous shard lists before training; `data_split_num` groups sequentially and does not rebalance languages or durations.

## Distributed config surprises

| Symptom | Explanation | Recovery |
|---|---|---|
| Nested `train_conf.use_deepspeed=true` seems ignored. | Top-level `++use_deepspeed=false` takes precedence over nested `train_conf`. | Put intentional engine choices at top level and remove conflicting nested keys. |
| DDP starts when no engine was requested. | With `WORLD_SIZE > 1`, DDP is automatic when DeepSpeed and FSDP are both false. | Launch single process for non-distributed smoke, or intentionally enable DeepSpeed/FSDP. |
| DeepSpeed and FSDP conflict. | `use_deepspeed` and `use_fsdp` are mutually exclusive. | Choose one engine. Do not set both top-level or nested. |
| DeepSpeed config path not used. | A top-level `++deepspeed_config=...` overrides nested `train_conf.deepspeed_config`. | Keep exactly one value, preferably top-level when using DeepSpeed. |

## Checkpoint pruning and validation

Symptoms:

- An unvalidated checkpoint file exists but is absent from best-checkpoint ranking.
- A worse validated checkpoint was pruned while an unvalidated file remains on disk.
- The averaged checkpoint does not include every saved checkpoint.

Expected behavior:

- Ranking uses validation metrics from `val_acc_step_or_epoch` or `val_loss_step_or_epoch`.
- `avg_keep_nbest_models_type=acc` means larger is better.
- `avg_keep_nbest_models_type=loss` means smaller is better.
- A checkpoint saved at a step with no validation metric is kept on disk but excluded from `saved_ckpts` and should not evict a validated best checkpoint.

Recoveries:

- Align `train_conf.save_checkpoint_interval` and `train_conf.validate_interval` if every saved checkpoint should be ranked.
- Inspect logs for messages that a checkpoint has no metric and is excluded from ranking.
- Increase `train_conf.keep_nbest_models` if validated checkpoints are pruned too aggressively.
- Choose `avg_keep_nbest_models_type=loss` only when the validation loss is the intended criterion.

## Local inference after training fails

| Symptom | Likely cause | Recovery |
|---|---|---|
| Local model directory is not loadable by `++model=...`. | `configuration.json` is missing. | Use `python -m funasr.bin.inference --config-path ... --config-name ... ++init_param=...` with explicit token and CMVN files. |
| Token or CMVN file not found. | Paths stored in `config.yaml` point to a different machine or moved artifact. | Override `++tokenizer_conf.token_list` and `++frontend_conf.cmvn_file` with paths valid in the current session. |
| Output is empty or written somewhere unexpected. | `++input` or `++output_dir` is wrong, or Hydra quoting caused an override to be ignored. | Print the exact command, quote values with spaces, and test a single local WAV first. |

## Export and ONNX issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| `funasr-export` fails before export starts. | Model id/local directory is wrong, or optional model dependencies are missing. | First run import/help checks, then load the model with `AutoModel(..., device="cpu")` if a live load is authorized. |
| Quantized export fails or produces poor results. | Calibration input/count is inadequate or the model path does not support that quantization route. | Retry non-quantized export, then add representative `++input` and tune `++calib_num` only if quantization is required. |
| ONNX optimization command is missing. | `onnxslim` is optional. | Install it only when the user asks to optimize ONNX artifacts. |
| ONNX runtime import unexpectedly pulls in `torch`. | The wrong package or environment is being inspected. | Use the separate ONNX runtime package and verify its install requirements are torch-free. |
| Missing normalizer or CUDA/C++ data files from a wheel. | Package data was not included in the built wheel. | Inspect wheel contents; fix packaging data rather than changing export or inference flags. |

## Optional dependency reminders

- vLLM is optional and belongs to `../llm-asr-and-vllm/`.
- Serving dependencies and server startup belong to `../serving-and-runtime/`.
- Fuzzy hotword dependencies are unrelated to training manifests; explicit manifest fields should still be testable without them.
