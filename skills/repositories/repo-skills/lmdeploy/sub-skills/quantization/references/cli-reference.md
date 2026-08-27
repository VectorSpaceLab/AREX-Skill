# LMDeploy Quantization CLI Reference

This reference covers planning and validating LMDeploy quantization commands. Commands shown here are intended to be adapted to the user's model, storage location, GPU backend, and network policy.

## Lite Command Map

| Goal | Command | Output | Notes |
| --- | --- | --- | --- |
| AWQ W4A16 artifact | `lmdeploy lite auto_awq MODEL --work-dir OUT` | Hugging Face-style quantized directory | LMDeploy Lite's built-in AWQ path. Use `--model-format awq` when loading with TurboMind if auto-detection is not enough. |
| GPTQ W4A16 artifact | `lmdeploy lite auto_gptq MODEL --work-dir OUT` | GPTQ quantized directory | Requires the `auto-gptq` package. Use `--model-format gptq` when loading if needed. |
| Calibration statistics only | `lmdeploy lite calibrate MODEL --work-dir OUT` | Calibration statistics such as activation stats | Useful when debugging calibration support or scale search, not normally the final runtime artifact. |
| SmoothQuant W8A8/FP8 artifact | `lmdeploy lite smooth_quant MODEL --work-dir OUT --quant-dtype int8` | SmoothQuant quantized directory | Use `--quant-dtype int8`, `fp8`, `float8_e4m3fn`, or `float8_e5m2`; bit width must match the dtype. |

## Shared Calibration Flags

| Flag | Default | Applies To | Guidance |
| --- | --- | --- | --- |
| `MODEL` | required | all lite commands | Local Hugging Face directory or model ID. Remote IDs may download weights and datasets. |
| `--work-dir` | `./work_dir` | all lite commands | Always set explicitly. Include model name and quant type, for example `internlm2_5-7b-chat-awq-4bit`. |
| `--calib-dataset` | `wikitext2` | all calibration-backed commands | Choices include `wikitext2`, `c4`, `pileval`, `gsm8k`, `neuralmagic_calibration`, `open-platypus`, `openwebtext`. |
| `--calib-samples` | `128` | all calibration-backed commands | Set `0` for AWQ data-free mode. More samples can improve stability but increase runtime and dataset reads. |
| `--calib-seqlen` | `2048` | all calibration-backed commands | Reduce first when calibration OOMs. Increase only when long-context quality matters and memory allows. |
| `--batch-size` | `1` | all calibration-backed commands | Keep `1` for constrained memory; larger values can reduce time but increase VRAM. |
| `--search-scale` | disabled | `auto_awq`, `calibrate`, `smooth_quant` | Enables scale-ratio search. Try when quality is degraded, but expect slower calibration and more memory pressure. |
| `--dtype` | `auto` | all lite commands | `auto`, `float16`, or `bfloat16`; ignored by some quantized model loads. Use `float16` if BF16 is unsupported. |
| `--trust-remote-code` | disabled | all lite commands | Use only when the selected model requires custom remote code and the user accepts that trust boundary. |

## AWQ Flags

`lmdeploy lite auto_awq MODEL --work-dir OUT` supports:

- `--device cuda|npu`: quantization device, default `cuda`.
- `--w-bits`: default `4`.
- `--w-group-size`: default `128`.
- `--w-sym`: enable symmetric quantization; default is asymmetric (`zero_point=True`).
- `--revision` and `--download-dir`: select or cache a remote model revision.

Typical AWQ command:

```shell
lmdeploy lite auto_awq internlm/internlm2_5-7b-chat \
  --work-dir internlm2_5-7b-chat-awq-4bit \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1 \
  --w-bits 4 \
  --w-group-size 128
```

Load the output with TurboMind:

```shell
lmdeploy chat ./internlm2_5-7b-chat-awq-4bit --backend turbomind --model-format awq
lmdeploy serve api_server ./internlm2_5-7b-chat-awq-4bit --backend turbomind --model-format awq
```

Python handoff:

```python
from lmdeploy import TurbomindEngineConfig, pipeline

pipe = pipeline(
    "./internlm2_5-7b-chat-awq-4bit",
    backend_config=TurbomindEngineConfig(model_format="awq"),
)
print(pipe(["Hi", "Shanghai is"]))
```

## GPTQ Flags

`lmdeploy lite auto_gptq MODEL --work-dir OUT` supports:

- `--w-bits`: default `4`.
- `--w-group-size`: default `128`.
- `--calib-dataset`, `--calib-samples`, `--calib-seqlen`, and `--batch-size`.
- `--dtype`, `--revision`, and `--trust-remote-code`.

GPTQ uses `auto-gptq`. The LMDeploy wrapper uses `desc_act=False` and `sym=True`, because those are the supported settings for LMDeploy loading.

Typical GPTQ command:

```shell
lmdeploy lite auto_gptq /models/source-model \
  --work-dir /models/source-model-gptq-4bit \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1 \
  --w-bits 4 \
  --w-group-size 128
```

Load the output with `--model-format gptq`, not `awq`:

```shell
lmdeploy chat /models/source-model-gptq-4bit --backend turbomind --model-format gptq
lmdeploy serve api_server /models/source-model-gptq-4bit --backend turbomind --model-format gptq
```

## Calibrate Flags

`lmdeploy lite calibrate MODEL --work-dir OUT` creates calibration statistics rather than a final quantized model. Use it to debug supported architecture mappings, dataset access, calibration memory, and scale collection.

Common command:

```shell
lmdeploy lite calibrate /models/source-model \
  --work-dir /models/source-model-calibration \
  --calib-dataset wikitext2 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1
```

## SmoothQuant and FP8 Flags

`lmdeploy lite smooth_quant MODEL --work-dir OUT --quant-dtype DTYPE` supports:

- `--quant-dtype int8`: W8A8 INT8 path.
- `--quant-dtype fp8` or `float8_e4m3fn`: FP8 E4M3 path.
- `--quant-dtype float8_e5m2`: FP8 E5M2 path.
- `--device cuda|npu`: default `cuda`.
- `--search-scale`: slower but can improve scaling.

The implementation asserts that the quantized dtype bit width matches `--w-bits`; use `--w-bits 8` with `int8` and FP8 dtypes.

Typical INT8 command:

```shell
lmdeploy lite smooth_quant internlm/internlm2_5-7b-chat \
  --work-dir internlm2_5-7b-chat-int8 \
  --quant-dtype int8 \
  --calib-samples 128 \
  --calib-seqlen 2048 \
  --batch-size 1
```

Typical FP8 command:

```shell
lmdeploy lite smooth_quant internlm/internlm2_5-7b-chat \
  --work-dir internlm2_5-7b-chat-fp8 \
  --quant-dtype fp8 \
  --w-bits 8
```

SmoothQuant outputs are loaded through the PyTorch backend in the documented path:

```shell
lmdeploy serve api_server ./internlm2_5-7b-chat-int8 --backend pytorch
```

Python handoff:

```python
from lmdeploy import PytorchEngineConfig, pipeline

pipe = pipeline("./internlm2_5-7b-chat-int8", backend_config=PytorchEngineConfig(tp=1))
print(pipe(["Hi", "Shanghai is"]))
```

## KV Cache Quantization Policies

KV quantization is online inference-time quantization, not a saved-weight conversion. Set `quant_policy` in CLI or engine config.

| Value | Alias | Backend Notes | Meaning |
| --- | --- | --- | --- |
| `0` | `none` | PyTorch and TurboMind | No KV-cache quantization. |
| `4` | `int4` | PyTorch and TurboMind on supported devices | 4-bit KV cache; higher memory savings with more accuracy risk. |
| `8` | `int8` | PyTorch and TurboMind on supported devices | 8-bit KV cache; safer first choice. |
| `16` | `fp8`, `fp8_e4m3` | PyTorch only | FP8 E4M3 KV cache; TurboMind rejects FP8 policies. |
| `17` | `fp8_e5m2` | PyTorch only | FP8 E5M2 KV cache; TurboMind rejects FP8 policies. |
| `42` | `turbo_quant` | PyTorch only | TurboQuant K=4bit QJL4 and V=2bit MSE. |

CLI examples:

```shell
lmdeploy chat internlm/internlm2_5-7b-chat --backend turbomind --quant-policy 8
lmdeploy serve api_server internlm/internlm2_5-7b-chat --backend turbomind --quant-policy int8
lmdeploy serve api_server Qwen/Qwen3-8B --backend pytorch --quant-policy turbo_quant
```

Python examples:

```python
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig, pipeline

pipe_tm = pipeline("internlm/internlm2_5-7b-chat", backend_config=TurbomindEngineConfig(quant_policy=8))
pipe_pt = pipeline("Qwen/Qwen3-8B", backend_config=PytorchEngineConfig(quant_policy=42, cache_max_entry_count=0.8))
```

## Validation Commands

Safe syntax checks that do not start quantization:

```shell
lmdeploy lite auto_awq --help
lmdeploy lite smooth_quant --help
lmdeploy lite auto_gptq --help
lmdeploy lite calibrate --help
```

Runtime validation after quantization requires the target hardware and model weights:

```shell
lmdeploy chat OUT_DIR --backend turbomind --model-format awq
lmdeploy serve api_server OUT_DIR --backend turbomind --model-format awq --server-port 23333
```
