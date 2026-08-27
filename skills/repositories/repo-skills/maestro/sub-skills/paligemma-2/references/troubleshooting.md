# PaliGemma 2 troubleshooting

This reference covers the PaliGemma 2 recipe only. For dataset-layout and metric-registry problems, route to [datasets-and-metrics](../../datasets-and-metrics/).

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` or `ModuleNotFoundError` for `bitsandbytes` during `qlora` setup | The quantized path requires bitsandbytes support | Install the PaliGemma extra or use `lora` / `freeze` instead of `qlora`. QLoRA is the only strategy here that truly depends on 4-bit quantization. |
| CUDA out-of-memory during load or training | Batch size, model size, or `max_new_tokens` are too large for the device | Reduce `--batch_size`, keep or increase gradient accumulation, lower `--max_new_tokens`, or switch from `qlora`/full fine-tuning to `lora` or `freeze`. |
| `ValueError: Requested device '...' is not available.` | `PaliGemma2Configuration.__post_init__` validates the device string | Use `auto` or a backend the host really exposes (`cpu`, `cuda`, `mps`, etc.). |
| Training returns without fitting | The dataset path or identifier could not be resolved | Confirm the dataset directory exists and has the expected split layout before calling `train`. Use the sibling dataset skill for full validation. |
| CLI `train` fails when `--peft_advanced_params` is omitted | Current entrypoint path expects a parsed PEFT dict variable to exist | Pass `--peft_advanced_params '{}'` on the CLI or use the Python API, which accepts omitted `peft_advanced_params`. |
| JSON extraction output is malformed or truncated | The prompt/suffix is too long, or `max_new_tokens` is too small | Increase `max_new_tokens`, shorten the prompt, and check that the dataset suffix is valid JSON text. |
| Generated text contains duplicate `<image>` tokens | `<image>` was already embedded in the dataset prefix | Remove `<image>` from dataset entries; Maestro prepends it internally in train, validation, and prediction code paths. |
| `json.loads(predict(...))` fails on an inference sample | The model prediction is not valid JSON yet | Inspect the training data for invalid targets, increase data quality, or treat the output as plain text until the model is better trained. |
| `load_model(...)` cannot find a checkpoint | The run directory naming or checkpoint path is wrong | Look under `./training/paligemma_2/<run>/checkpoints/latest` or the configured `output_dir` equivalent. |
| Metrics do not appear in the run directory | No metrics were requested or the names were unsupported | Use supported text metrics such as `edit_distance` or `bleu` for extraction tasks. Unsupported metric names are rejected by the common metric registry. |

## Common fixes

### QLoRA-specific failures

`OptimizationStrategy.QLORA` loads the base model with a 4-bit `BitsAndBytesConfig`. If that path fails:

1. Verify bitsandbytes is installed in the environment that is running Maestro.
2. Verify the device supports CUDA-style quantized inference/training.
3. If the goal is to fine-tune on a smaller footprint rather than quantize, fall back to `lora`.
4. If only the visual front-end should be frozen, use `freeze` instead of `qlora`.

### Hugging Face access or local checkpoint loading

`load_model(...)` calls `from_pretrained(...)` for both the processor and the model. If loading fails:

- Confirm the model id or local path is correct.
- Confirm the revision exists.
- If the model is gated or private, authenticate outside this skill and retry.
- If you are reloading a Maestro checkpoint, point `model_id_or_path` at the saved `checkpoints/latest` directory created by the trainer callback.

### CLI parsing and command generation

The bundled config helper can generate a safe command string. Use it when you want a reproducible command without typing every option by hand:

```bash
python scripts/build_paligemma_config.py \
  --dataset ./dataset \
  --metric edit_distance \
  --metric bleu \
  --emit cli
```

If `maestro paligemma_2 train` complains about an invalid JSON string for PEFT parameters, make sure the value is a JSON object string, not a Python dict literal.

### Validation and dataset formatting

For PaliGemma 2, the dataset contract is simple:

- `prefix` carries the task instruction.
- `suffix` carries the expected answer.
- `image` points to the image filename within the split directory.
- `<image>` is added by Maestro internally.

If any of those are wrong, fix the dataset first. Do not keep adding prompt tokens to compensate.

### Checkpoints and metrics

The trainer callback refreshes `checkpoints/latest` at the end of each epoch and saves plots under `metrics/` after training. If those are missing:

- Confirm training actually reached the end of at least one epoch.
- Confirm the configured `output_dir` is writable.
- Confirm the run directory was created under the expected base output path.
- Re-run with a smaller batch size or shorter sequences if the process was interrupted by memory pressure.

## When to route away

Use the sibling dataset skill when the issue is about:

- missing `train` / `valid` / `test` splits,
- invalid JSONL lines,
- missing image files,
- Roboflow dataset resolution,
- supported metrics or metric naming.

Use another model skill when the user actually needs detection-format conversion or a dedicated object-detection formatter. PaliGemma 2's source in Maestro does not provide that API.
