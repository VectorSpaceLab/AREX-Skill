# Quantization Troubleshooting

Use this guide when an LMDeploy Lite command fails, a quantized artifact cannot be loaded, or KV-cache quantization behaves unexpectedly.

## OOM During Calibration

Symptoms:

- CUDA out-of-memory during `lmdeploy lite auto_awq`, `calibrate`, or `smooth_quant`.
- Process dies while loading calibration samples or concatenating calibration tensors.
- Larger models fail even with apparently small sample counts.

Recovery:

1. Keep `--batch-size 1`.
2. Reduce `--calib-seqlen` before reducing `--calib-samples`.
3. Disable `--search-scale` for the first successful artifact.
4. Use `--dtype float16` if BF16 is selected automatically but unsupported.
5. Close any existing LMDeploy pipelines or servers before running quantization.
6. If using AWQ, consider `--calib-samples 0` only when the user accepts data-free quality risk.

## Insufficient Disk While Saving Weights

Symptoms:

- Errors during `save_pretrained`, `save_quantized`, or tokenizer save.
- Partial output directory with missing `config.json`, tokenizer files, or safetensors.
- Filesystem quota or no-space-left errors.

Recovery:

1. Delete the partial `--work-dir` before retrying.
2. Ensure enough free space for a copied model artifact plus temporary calibration files.
3. Use a dedicated output directory outside the source model directory.
4. Keep the original source model until the quantized artifact has passed a load smoke test.

## `flash_attn` Missing For Qwen

Symptoms:

- Runtime error saying Qwen requires `pip install flash-attn` for calibration/quantification.
- Failure occurs before useful calibration statistics are exported.

Recovery:

1. Install a `flash-attn` build compatible with the active Python, PyTorch, CUDA, and compiler stack.
2. If installation is not feasible, choose a model architecture that does not require this path or use an environment prepared for Qwen quantization.
3. Do not spend time tuning calibration flags until the import dependency is resolved.

## AWQ/GPTQ Model-Format Mismatch

Symptoms:

- Quantized model loads but produces bad outputs or fails during TurboMind initialization.
- User passes `--model-format awq` for a GPTQ output or `--model-format gptq` for an AWQ output.
- The output directory name does not indicate the quantization type.

Recovery:

1. Identify the quantization command that created the artifact.
2. Use `--model-format awq` for `lmdeploy lite auto_awq` outputs.
3. Use `--model-format gptq` for `lmdeploy lite auto_gptq` outputs.
4. Rename or recreate ambiguous output directories with explicit suffixes such as `-awq-4bit` or `-gptq-4bit`.
5. If the artifact came from `llm-compressor`, inspect whether it is AWQ, GPTQ, or compressed-tensors style before forcing a format.

## Work Directory And Chat Template Issues

Symptoms:

- Quantized model loads but chat formatting is wrong.
- CLI asks for or misidentifies a chat template.
- Output directory is named generically, such as `work_dir` or `4bit`.

Recovery:

1. Use a `--work-dir` that includes the base model name and quantization type.
2. If the chat template is still ambiguous, pass an explicit `--chat-template` or `ChatTemplateConfig` through the inference workflow.
3. Route deeper chat-template debugging to `pipeline-inference`.

## Unsupported GPU Or Backend

Symptoms:

- TurboMind rejects FP8 KV-cache quantization.
- PyTorch backend rejects a non-CUDA/non-Ascend `device_type` when `quant_policy > 0`.
- FP8 conversion fails on older GPUs.
- INT4/INT8 inference is attempted on unsupported hardware.

Recovery:

1. Use TurboMind KV policies only for `0`, `4`, `8`, or `42` where supported; avoid `16` and `17` with TurboMind.
2. Use PyTorch backend for FP8 KV-cache policies `16` and `17`.
3. Use PyTorch backend for TurboQuant policy `42`, and avoid speculative decoding and MLA models.
4. For W8A8/FP8 SmoothQuant outputs, prefer documented PyTorch backend load commands.
5. Check the GPU architecture before promising INT4/INT8/FP8 acceleration.

## Expensive Or Network Datasets

Symptoms:

- Calibration stalls while downloading a dataset.
- Offline environment fails on `wikitext2`, `c4`, `pileval`, `neuralmagic_calibration`, `open-platypus`, or `openwebtext`.
- User expected no network access.

Recovery:

1. Ask whether remote dataset download is allowed before running quantization.
2. Use a cached or approved dataset when network is restricted.
3. Lower `--calib-samples` for a quick smoke artifact, then rerun with a quality-oriented sample count if accepted.
4. Document the dataset and sample count in the artifact handoff.

## `auto_gptq` Dependency Missing

Symptoms:

- Import error: install `auto-gptq` to use `auto_gptq`.
- GPTQ command fails before model loading.

Recovery:

1. Install `auto-gptq` in the quantization environment if GPTQ is required.
2. If dependency installation is not allowed, switch to AWQ only after confirming with the user.
3. Keep the output format and handoff commands aligned with the final algorithm.

## SmoothQuant Dtype Mismatch

Symptoms:

- Assertion failure around dtype bit width.
- User passes `--quant-dtype int8` with a non-8 `--w-bits` value.

Recovery:

1. Use `--w-bits 8` for `int8`, `fp8`, `float8_e4m3fn`, and `float8_e5m2`.
2. Use `auto_awq` or `auto_gptq` for 4-bit weight-only artifacts.
3. Do not use SmoothQuant as a substitute for AWQ/GPTQ W4A16 output.

## TurboQuant Caveats

Symptoms:

- TurboQuant policy fails with PyTorch pipeline/server creation.
- Workload uses speculative decoding or an MLA architecture.
- Performance is slower than expected.

Recovery:

1. Confirm backend is PyTorch, not TurboMind.
2. Confirm the model head dimension is a power of two.
3. Disable speculative decoding.
4. Avoid MLA models for TurboQuant.
5. Install `fast_hadamard_transform` only if the user wants the optional performance improvement and environment mutation is allowed.

## Safe Escalation Questions

Ask before continuing when:

- The next step installs `auto-gptq`, `llmcompressor`, `flash-attn`, or `fast_hadamard_transform`.
- The command will download model weights or calibration datasets.
- The planned run can occupy a large GPU for a long time.
- The artifact would overwrite an existing `--work-dir`.
- Hardware support is unclear and a failed quantization run would be expensive.
