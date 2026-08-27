# Troubleshooting

## Missing LLaMA conversion
**Symptom:** `from_pretrained()` cannot find a config, tokenizer, or weight file in `path_raw`.

**Fix:** Convert Meta's released LLaMA checkpoint to Hugging Face format first, then point `path_raw` at the converted directory. A valid directory should contain a config file, tokenizer assets, and one or more weight files.

## Tokenizer mismatch or missing pad token
**Symptom:** embedding-shape errors, tokenizer warnings, or a size mismatch during subtraction or addition.

**Fix:** Make sure the raw checkpoint and the tuned/diff checkpoint were built with compatible tokenizers. If the raw tokenizer has no pad token, let the resize helper add `[PAD]` and resize both embedding matrices before arithmetic.

## Missing weight diff artifacts
**Symptom:** `path_diff` is empty, points at the wrong directory, or does not contain model/tokenizer files.

**Fix:** Confirm that `path_diff` is the released Alpaca diff directory, not the raw checkpoint or an output directory that was never populated. Re-download or re-export the diff if the model files are missing.

## No recovered output directory
**Symptom:** recovery runs, but no files appear on disk.

**Fix:** Confirm that `path_tuned` was provided. The recover flow only saves when `path_tuned` is not `None`; otherwise the result stays in memory only.

## OOM or high-RAM pressure
**Symptom:** load stalls, CUDA OOM, or host memory pressure while loading float32 checkpoints.

**Fix:** Use the dry-run path builder first. For real execution, prefer CPU only when you just need inspection, or a sufficiently large CUDA host when you actually want recovery. Keep `low_cpu_mem_usage=True`, but remember the checkpoints are still large.

## Integrity checksum failure
**Symptom:** the naive checksum assertion fails with a value other than `50637.1836`.

**Fix:** This usually means the raw/diff pair is mismatched, a file is corrupted, or the checkpoint was modified. Re-check the path roles, re-download the artifacts, and rerun. The checksum is heuristic only, so a pass is helpful but not sufficient for end-to-end correctness.

## Hugging Face access issues
**Symptom:** `from_pretrained()` tries to reach the hub, returns auth errors, or cannot find gated weights.

**Fix:** Keep the workflow local when possible. If you intentionally rely on Hub resolution, authenticate first and make sure the model access terms allow it. Otherwise convert or mirror the checkpoint locally and rerun in offline mode.

## Device errors
**Symptom:** invalid device strings, CUDA visibility problems, or the model does not fit on the selected accelerator.

**Fix:** Use `device=cpu` for planning and inspection. Only choose `cuda` if the hardware is visible and large enough for float32 loading. The command builder can emit the dry-run command first so you can confirm the path roles before touching the device.

## Inference smoke surprises
**Symptom:** `test_inference=True` prints a poor completion, times out, or fails after the model has loaded.

**Fix:** Remember the smoke test is only a qualitative sanity check. Disable it when you only need recovery, or rerun with a smaller prompt and more memory. A strange completion does not by itself imply bad weights.
