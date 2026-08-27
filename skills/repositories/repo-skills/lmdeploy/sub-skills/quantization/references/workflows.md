# Quantization Workflows

Use these workflows to plan quantized artifact creation without confusing quantization, inference, and serving responsibilities.

## Workflow 1: Memory-Constrained AWQ Artifact

Use when a user wants a 4-bit W4A16 artifact and has limited GPU memory.

1. Confirm the source model is a local Hugging Face directory or an allowed remote model ID.
2. Choose an explicit output directory such as `model-name-awq-4bit`.
3. Start with conservative calibration settings: `--batch-size 1`, `--calib-seqlen 2048`, `--calib-samples 128`.
4. If OOM occurs, reduce `--calib-seqlen` first, keep `--batch-size 1`, and only then reduce `--calib-samples`.
5. If quality is poor and memory allows, retry with `--search-scale` and possibly a larger `--batch-size`.
6. Handoff the output as AWQ: use `--model-format awq` for chat, pipeline, and serving when format auto-detection is uncertain.

Command skeleton:

```shell
lmdeploy lite auto_awq SOURCE_MODEL \
  --work-dir OUT_AWQ_DIR \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1 \
  --w-bits 4 \
  --w-group-size 128
```

Validation handoff:

```shell
lmdeploy chat OUT_AWQ_DIR --backend turbomind --model-format awq
lmdeploy serve api_server OUT_AWQ_DIR --backend turbomind --model-format awq
```

## Workflow 2: GPTQ Artifact Without AWQ/GPTQ Confusion

Use when the user explicitly asks for GPTQ or already has a GPTQ target format.

1. Check that `auto-gptq` is installed or include it as a prerequisite.
2. Keep `--w-bits 4` and `--w-group-size 128` unless the user has a tested alternative.
3. Use the same calibration dataset controls as AWQ.
4. Name the output with `gptq`, such as `model-name-gptq-4bit`.
5. Load with `--model-format gptq`, not `awq`.

Command skeleton:

```shell
lmdeploy lite auto_gptq SOURCE_MODEL \
  --work-dir OUT_GPTQ_DIR \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1 \
  --w-bits 4 \
  --w-group-size 128
```

Validation handoff:

```shell
lmdeploy chat OUT_GPTQ_DIR --backend turbomind --model-format gptq
lmdeploy serve api_server OUT_GPTQ_DIR --backend turbomind --model-format gptq
```

## Workflow 3: SmoothQuant INT8 or FP8

Use when the user wants W8A8 or FP8 rather than weight-only INT4.

1. Choose `--quant-dtype int8` for INT8, or `fp8`/`float8_e4m3fn`/`float8_e5m2` for FP8.
2. Keep `--w-bits 8`; the implementation checks that the dtype bit width matches `--w-bits`.
3. Expect PyTorch backend loading in the documented path.
4. For Qwen legacy architecture failures, check for `flash_attn` before spending time on data settings.

Command skeleton:

```shell
lmdeploy lite smooth_quant SOURCE_MODEL \
  --work-dir OUT_INT8_OR_FP8_DIR \
  --quant-dtype int8 \
  --w-bits 8 \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1
```

Validation handoff:

```shell
lmdeploy chat OUT_INT8_OR_FP8_DIR --backend pytorch
lmdeploy serve api_server OUT_INT8_OR_FP8_DIR --backend pytorch
```

## Workflow 4: KV Cache Quantization Only

Use when the user does not want a new weight artifact and only wants less KV-cache memory during inference or serving.

1. Do not run `lmdeploy lite`; KV-cache quantization is online.
2. Pick a policy:
   - `8` / `int8`: safer first choice.
   - `4` / `int4`: more memory savings, higher accuracy risk.
   - `16` / `fp8`: PyTorch-only FP8 E4M3.
   - `17` / `fp8_e5m2`: PyTorch-only FP8 E5M2.
   - `42` / `turbo_quant`: PyTorch-only TurboQuant K4/V2.
3. For TurboMind, avoid policies `16` and `17`; the config rejects FP8 KV cache for TurboMind.
4. For PyTorch, keep `device_type` on `cuda` or `ascend` when `quant_policy > 0`.
5. For TurboQuant, avoid Multi-head Latent Attention, speculative decoding, and non-power-of-two head dimensions.

CLI examples:

```shell
lmdeploy chat MODEL --backend turbomind --quant-policy int8
lmdeploy serve api_server MODEL --backend pytorch --quant-policy turbo_quant
```

Python examples:

```python
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig, pipeline

pipe = pipeline("MODEL", backend_config=TurbomindEngineConfig(quant_policy=8))
pipe_turbo = pipeline("MODEL", backend_config=PytorchEngineConfig(quant_policy=42))
```

## Workflow 5: Quantized Artifact Handoff

Use after any artifact has been written.

1. Record the source model, quantization command, output directory, quantization type, calibration dataset, sample count, sequence length, batch size, and optional trust boundary.
2. Record whether any remote model or calibration dataset download was required.
3. Provide one offline inference command and one server command, but route deeper inference and API details to the relevant sub-skill.
4. Include a model-format warning when the output is AWQ or GPTQ.
5. Include a smoke-test prompt and expected success condition: model loads and returns non-empty text.

Minimum handoff for AWQ:

```shell
lmdeploy chat OUT_AWQ_DIR --backend turbomind --model-format awq
lmdeploy serve api_server OUT_AWQ_DIR --backend turbomind --model-format awq --server-port 23333
```

Minimum handoff for SmoothQuant:

```shell
lmdeploy chat OUT_INT8_DIR --backend pytorch
lmdeploy serve api_server OUT_INT8_DIR --backend pytorch --server-port 23333
```

## Workflow 6: Before Running Expensive Quantization

Ask or verify these points before starting long GPU work:

- Does the user allow remote model and dataset downloads?
- Is there enough disk for a full copied quantized checkpoint plus calibration artifacts?
- Is the target GPU architecture supported for the chosen format?
- Is `trust_remote_code` acceptable for this model?
- Should calibration favor quality (`--search-scale`, more samples, longer seqlen) or fit/time (`--batch-size 1`, shorter seqlen)?
- Does the user need AWQ, GPTQ, SmoothQuant INT8/FP8, or only online KV-cache quantization?

## Validation Ladder

Start from low-cost checks and climb only when hardware and weights are available.

1. CLI syntax: `lmdeploy lite auto_awq --help`, `lmdeploy lite smooth_quant --help`.
2. Planner check: run `scripts/plan_quantization_command.py` with the intended options.
3. Quantization dry planning: confirm output directory, disk budget, dataset policy, and model-format handoff.
4. Quantization run: execute the selected `lmdeploy lite` command.
5. Load smoke test: `lmdeploy chat OUT_DIR ...` or a tiny `pipeline()` prompt.
6. Serving smoke test: `lmdeploy serve api_server OUT_DIR ...` followed by a simple client request handled by `serving-apis`.
7. Accuracy/performance evaluation: use a user-approved benchmark or OpenCompass-style evaluation outside this runtime skill.
