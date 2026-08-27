# Integration Workflows

Quantization in Transformers is usually an integration problem: the config class is small, but correctness depends on Accelerate placement, PEFT adapter semantics, distributed strategy, kernels, serving options, and checkpoint metadata.

## No-download Planning Workflow

1. Determine the model artifact type: regular Transformers checkpoint, pre-quantized Transformers checkpoint, adapter repository, GGUF file, or local converted weights.
2. Determine execution path: inference script, `pipeline(...)`, generation loop, Trainer/QLoRA, `transformers serve`, or custom service.
3. Select the quantization method from [quantization methods](quantization-methods.md).
4. Check [compatibility](compatibility.md) for packages, hardware, serialization, and integration conflicts.
5. Run `scripts/quantization_config_smoke.py` for config construction before any model download.
6. Only then write model-loading code or install backend packages.

## Accelerate And Device Maps

`device_map="auto"` is the common companion for large quantized models because it asks Accelerate to place modules across available devices.

```python
model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=quantization_config,
    device_map="auto",
    dtype="auto",
)
```

Preflight checks:

- Install `accelerate` for `device_map` and large-model dispatch.
- Use `max_memory={0: "20GiB", "cpu": "48GiB"}` when automatic placement overfills a device.
- Avoid mixing `device_map` with tensor parallel `tp_plan`; they solve different partitioning problems and can conflict at weight loading.
- For CPU offload, explain which weights stay fp32 and where the offload folder or CPU RAM pressure appears.
- Check that skipped modules, tied weights, and `lm_head` placement remain compatible with generation.

## PEFT And QLoRA

For memory-efficient fine-tuning, quantize the base model and train adapters rather than updating quantized base weights.

```python
from peft import LoraConfig
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

base_model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=BitsAndBytesConfig(load_in_4bit=True),
    device_map="auto",
    dtype="auto",
)
base_model.add_adapter(LoraConfig(r=8, lora_alpha=16), adapter_name="qlora")
```

Route dataset, `Trainer`, evaluation, checkpoints, and `TrainingArguments` details to [training](../../training/SKILL.md). Keep this sub-skill responsible for:

- Choosing quantization method and compute/storage dtype.
- Explaining that 4-bit/8-bit training generally updates extra adapter parameters, not the base quantized weights.
- Ensuring `peft >= 0.19.0` when using the integrated `PeftAdapterMixin` path.
- Checking FSDP/DeepSpeed save behavior for frozen quantized base weights and adapter-only checkpoints.
- Verifying adapter repositories include `adapter_config.json` and match the base model.

## DeepSpeed

Use DeepSpeed when the task is distributed training or memory partitioning, not simply loading a single quantized checkpoint. Common interactions:

- ZeRO-3 can shard model states and optimizer states; PEFT adapter checkpoints should skip frozen base weights where supported.
- Quantized base + LoRA can reduce per-rank memory, but optimizer state savings mostly apply to trainable adapter parameters.
- Backend quantization kernels may not support every ZeRO/offload combination.
- DeepSpeed configuration belongs with [training](../../training/SKILL.md); this sub-skill should flag quantization compatibility and package constraints.

Expected agent output for a DeepSpeed + quantization request: identify trainable parameters, frozen quantized base, package list, ZeRO stage, offload choices, save/resume semantics, and one tiny smoke command before full training.

## FSDP

FSDP and quantization are sensitive to wrapping order and parameter dtypes.

- For QLoRA, let the training stack adjust mixed precision policy for quantization storage dtype when available.
- Avoid auto-wrapping quantized backend modules unless the backend documents FSDP support.
- If using torchao/FSDP2, require matching PyTorch, torchao, and Accelerate support.
- If full-parameter saving fails, save adapter-only or move model to a supported device/dtype first.

When the user's task is ordinary distributed fine-tuning, route training arguments to [training](../../training/SKILL.md). Keep this sub-skill focused on whether the chosen quantized modules can be wrapped, sharded, saved, and resumed.

## Tensor Parallelism

Transformers native tensor parallelism uses `tp_plan="auto"` for supported models whose config exposes a tensor-parallel plan.

```python
from transformers import AutoConfig, AutoModelForCausalLM

config = AutoConfig.from_pretrained("org/model")
print(config.base_model_tp_plan is not None)

model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    dtype="auto",
    tp_plan="auto",
)
```

Quantization notes:

- Do not combine `tp_plan` with `device_map`; TP shards tensors while `device_map` places whole modules.
- Confirm the quantization backend supports sharded linear layers before adding `quantization_config` to TP loading.
- TP benefits fast intra-node links and usually multiple GPUs; it is not a CPU memory workaround.
- Some pre-quantized checkpoints encode module replacements that do not match TP sharding plans.

## Kernel Integrations

Kernel options can speed up quantized models but are rarely universal.

- AWQ fused modules can improve generation speed for supported Llama/Mistral-style architectures but may conflict with other attention optimizations.
- GPTQ Marlin is a specialized 4-bit CUDA kernel; check GPU architecture and symmetric/asymmetric checkpoint compatibility.
- `TorchAoConfig` can work well with `torch.compile`, but first inference may compile and repeated shape changes can recompile.
- Hub kernels use `KernelConfig` and `use_kernels=True`; validate model architecture and kernel mapping first.
- Liger kernels are primarily a training optimization through `TrainingArguments(use_liger_kernel=True)`, not a replacement for quantization config.

## Serving And Continuous Batching

Serving requests that mention quantization should usually involve both this sub-skill and [serving-cli](../../serving-cli/SKILL.md) or [generation](../../generation/SKILL.md).

Preflight checks for a quantized service:

- Confirm the serving stack supports the selected quantization backend in its model-loading path.
- Disable or simplify continuous batching when the backend cannot support paged KV cache, compile, or offload options.
- Avoid static `torch.compile` cache assumptions when batch sizes and `max_new_tokens` vary per request.
- Keep `device_map`, tensor parallelism, and offload decisions explicit; do not let a service silently choose conflicting placement.
- Validate one single-request generation path before enabling concurrent requests.

For continuous batching, keep generation settings in [generation](../../generation/SKILL.md). This sub-skill owns whether the quantized backend supports the KV cache, scheduler, compile, and offload options chosen by the service.

## Pipeline Integration

For `pipeline(...)`, route task-specific behavior to [inference-pipelines](../../inference-pipelines/SKILL.md). Quantization still enters through the model load:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=BitsAndBytesConfig(load_in_4bit=True),
    device_map="auto",
    dtype="auto",
)
tokenizer = AutoTokenizer.from_pretrained("org/model", use_fast=True)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
```

Do not pass quantization-only decisions as arbitrary pipeline kwargs unless the pipeline docs explicitly support them. Load the model first when the quantization config needs careful control.

## Checkpoint Save And Reload Workflow

1. Save tokenizer/processor and quantization-aware model files together when the method supports serialization.
2. Ensure `quantization_config.json` or model `config.json` metadata records the method.
3. If loaded with `device_map`, move the model to a single supported device before saving when required by the method.
4. Reload in a fresh process with the minimum expected packages installed.
5. Confirm `model.hf_device_map`, quantization config, and one tiny forward/generation path.

If serialization is unsupported or experimental for the chosen method, return that as a hard limitation rather than promising Hub push or local reload.
