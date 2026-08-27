# Adapters and Quantization

Use this reference when choosing LoRA/QLoRA/ReLoRA fields, deciding how quantization fits the adapter, or debugging PEFT/quantization compatibility before expensive Axolotl runs.

## Adapter Decision

| Goal | Config pattern | Notes |
| --- | --- | --- |
| Full fine-tune | Omit `adapter`, keep `load_in_4bit: false` and `load_in_8bit: false` | All trainable weights update; hardware and distributed setup are outside this sub-skill. |
| LoRA | `adapter: lora` plus `lora_r`, `lora_alpha`, targets | Can combine with `load_in_8bit: true` for 8-bit base loading. |
| QLoRA | `adapter: qlora` and `load_in_4bit: true` | Axolotl schema rejects QLoRA without 4-bit loading and rejects QLoRA with 8-bit/GPTQ in normal training. |
| Existing adapter | `lora_model_dir` | Use for continuing, inference, or merging a previously trained adapter. |
| ReLoRA | `relora: true` plus restart/prune fields | Applies restart/prune behavior to LoRA-style training; method-specific scheduling belongs with training recipe guidance. |
| Plugin adapter | `adapter: <plugin-name>` plus `plugins:` | Axolotl validates that a plugin registered the adapter capability and loader support. |

Use `axolotl merge-lora config.yaml` after training when the user wants a merged full model and the config points to the base model plus adapter output. Do not merge a QLoRA adapter while it is configured as 4-bit/8-bit/GPTQ loading; Axolotl validates these incompatibilities.

## LoRA Targeting

Prefer explicit targets for newer multimodal/MoE models.

Common fields:

```yaml
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
```

`lora_target_linear: true` asks Axolotl to discover linear-like modules. It is convenient on simple text Llama/Mistral/Qwen-style models, but risky on multimodal or MoE models because it can target vision/audio encoders or the wrong expert path. For multimodal configs, use a regex or explicit list restricted to the language backbone, for example `model.language_model.layers.[\d]+...` or `language_model.model.layers.[\d]+...` depending on the model wrapper.

When adding tokens or changing special tokens during adapter training, include embedding/head modules in `lora_modules_to_save` when Axolotl requests it. Llama/Mistral-style configs commonly need `embed_tokens` and `lm_head`.

## MoE Expert LoRA

Some MoE routed experts are not `nn.Linear` modules; they are 3D parameter tensors. Target them with `lora_target_parameters`:

```yaml
lora_target_parameters:
  - experts.gate_up_proj
  - experts.down_proj
lora_dropout: 0
```

Axolotl schema requires `lora_dropout: 0` when `lora_target_parameters` is set because PEFT parameter wrappers cannot apply non-zero dropout to expert parameters. For mixed configs, attention/MLP modules can still be in `lora_target_modules` while routed experts are in `lora_target_parameters`.

For MoE expert quantization, use:

```yaml
adapter: qlora
load_in_4bit: true
quantize_moe_experts: true
```

Axolotl rejects `quantize_moe_experts` without `adapter: lora`/`qlora`, without `load_in_4bit`/`load_in_8bit`, or with `lora_target_linear: true`. CUDA support is required; do not suggest this as a generic CPU/ROCm-safe setting.

ScatterMoE acceleration is a plugin/kernels path:

```yaml
plugins:
  - axolotl.integrations.kernels.KernelsPlugin
use_kernels: true
use_scattermoe: true
experts_implementation: scattermoe
```

Use it only when the model family and runtime support the expert interface. Without support, Axolotl warns and falls back to the native expert path.

## QLoRA and bitsandbytes

QLoRA baseline:

```yaml
adapter: qlora
load_in_4bit: true
bnb_config_kwargs:
  bnb_4bit_use_double_quant: true
```

Axolotl builds a `BitsAndBytesConfig` with 4-bit loading, NF4 quantization, double quantization, compute dtype from `torch_dtype`, and bfloat16 quant storage unless a model-specific override applies. Use `bnb_config_kwargs` for deliberate overrides rather than inventing unsupported top-level keys.

LoRA with 8-bit base loading:

```yaml
adapter: lora
load_in_8bit: true
```

Common failure modes:

- Missing bitsandbytes/CUDA backend: install/runtime issue, not a YAML syntax issue.
- `adapter: qlora` without `load_in_4bit: true`: Axolotl validation error.
- `adapter: qlora` with `load_in_8bit: true` or `gptq: true`: invalid for normal QLoRA loading.
- FSDP + QLoRA: route distributed loading and memory policy to `distributed-and-performance` after confirming adapter fields.

## Pre-Quantized and Load-Time Quantized Models

Axolotl model loading can use checkpoint-provided quantization config for adapters when the model config advertises `gptq`, `awq`, or `bitsandbytes`. It also supports explicit load-time model quantization config names:

```yaml
model_quantization_config: Mxfp4Config
model_quantization_config_kwargs: {}
```

or

```yaml
model_quantization_config: FineGrainedFP8Config
model_quantization_config_kwargs: {}
```

Treat these as advanced load-time settings; validate with `axolotl preprocess` and the exact installed Transformers/torchao stack.

Axolotl docs explicitly do not support GGUF/GPTQ/EXL2 as torchao PTQ output formats in the torchao quantize workflow. GPTQ/AWQ checkpoint loading is a separate pre-quantized-model path.

## QAT and PTQ with torchao

QAT trains with fake quantization, then a separate quantization command produces the quantized model:

```yaml
qat:
  activation_dtype: int8
  weight_dtype: int4
  group_size: 32
  fake_quant_after_n_steps: 100
```

Supported dtype aliases include `int4`, `int8`, `float8`/`fp8`, `nvfp4`, and `mxfp4` depending on the field and runtime stack. `weight_dtype` defaults to `int8`; `group_size` defaults to `32`.

After QAT, quantize using the same config:

```bash
axolotl quantize qat.yml
```

PTQ uses the top-level `quantization:` block:

```yaml
quantization:
  activation_dtype: int8
  weight_dtype: int4
  group_size: 256
  quantize_embedding: false
```

A quantized model is saved under the configured output directory’s quantized subdirectory. This sub-skill can advise the fields; actual accuracy/performance evaluation belongs to user-run experiments.

## LoRA Kernel Optimizations

LoRA kernels are enabled with:

```yaml
lora_mlp_kernel: true
lora_qkv_kernel: true
lora_o_kernel: true
```

Evidence shows support for common Llama/Mistral/Qwen/Gemma families, but not all architectures. Constraints:

- They require GPU/Triton-style runtime support.
- Targeted LoRA adapters cannot use dropout or bias for the optimized paths.
- They are not compatible with `trust_remote_code: true` in Axolotl validation.
- They are documented for SFT, not RLHF workflows.
- Gemma 4 has fused-attention paths and KV-sharing caveats; follow model-specific examples.

## Validation Checklist

Before training:

1. Confirm `adapter` matches quantization: QLoRA → `load_in_4bit: true`; LoRA+8bit → `load_in_8bit: true`; full fine-tune → no low-bit adapter fields.
2. For multimodal/MoE, avoid broad `lora_target_linear: true`; use explicit regex/list targets.
3. For routed experts, set `lora_target_parameters` and `lora_dropout: 0`.
4. For LoRA kernels, ensure no `trust_remote_code: true` and do not use them as a default for RLHF.
5. For QAT/PTQ, keep `qat:` and `quantization:` separate and use `axolotl quantize` only after QAT or for the PTQ workflow.
6. Run the bundled static checker, then `axolotl preprocess config.yaml` in the user’s environment.
