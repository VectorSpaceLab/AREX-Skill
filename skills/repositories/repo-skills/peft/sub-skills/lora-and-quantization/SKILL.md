---
name: lora-and-quantization
description: "Configure PEFT LoRA, LoRA variants, and quantized-base workflows,
  including QLoRA, LoftQ, QALoRA, trainable tokens, and quantization backend
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LoRA and Quantization

Use this sub-skill when the task is about choosing or debugging `LoraConfig`, AdaLoRA-like LoRA variants, LoRA initialization strategies, quantized base model preparation, or quantization backend compatibility in PEFT.

Do not use this sub-skill for adapter save/load/merge/conversion mechanics, distributed launcher configuration, or non-LoRA tuner families.

## Fast routing

- Need ordinary LoRA, QLoRA, DoRA, RS-LoRA, PiSSA, CorDA, EVA, OLoRA, LoftQ, QALoRA, aLoRA, LoRA-GA, MonteLoRA, VeLoRA, BdLoRA, Arrow routing, or trainable-token interactions: start here.
- Need `save_pretrained`, `from_pretrained`, `merge_and_unload`, PiSSA/CorDA/OLoRA conversion on save, adapter composition, or hotswapping: route to `save-load-merge`.
- Need `Trainer`, `Accelerate`, DeepSpeed, FSDP, launch commands, or dataset/training-loop integration: route to `training-and-integrations`.
- Need IA3, prompt tuning, OFT/BOFT, VeRA, LoHa/LoKr, Poly, FourierFT, or other non-LoRA tuners: route to `specialized-tuners`.

## Core LoRA checklist

1. Pick target layers before tuning hyperparameters.
   - For transformer QLoRA-style tuning, prefer `target_modules="all-linear"` so PEFT targets every linear/Conv1D layer except the output layer where applicable.
   - For smaller adapters, use architecture names such as `q_proj`, `k_proj`, `v_proj`, `o_proj`, `up_proj`, `down_proj`, `gate_proj`, `query`, `value`, or a regex string.
   - If PEFT cannot infer the architecture and `target_modules=None`, specify `target_modules` manually.
   - Use `target_modules=[]` only when intentionally using `target_parameters` for parameters that are not wrapped by a module `forward`, such as some MoE expert parameters.
2. Choose rank and scaling together.
   - `r` controls adapter capacity and memory.
   - `lora_alpha` controls LoRA scaling.
   - Default LoRA scales by `lora_alpha / r`; `use_rslora=True` scales by `lora_alpha / sqrt(r)` and is often better when raising `r`.
   - Use `rank_pattern` and `alpha_pattern` for layer-specific capacity instead of creating separate adapters.
3. Keep dropout and bias intentional.
   - `lora_dropout=0.0` is common for large language model instruction tuning; small data or overfitting may benefit from nonzero dropout.
   - `bias="none"` keeps adapter-disabled output closest to the base model. `bias="all"` or `"lora_only"` trains bias terms and can change outputs even when adapters are disabled.
4. Add task heads or tokens explicitly.
   - Use `modules_to_save` for randomly initialized heads such as classifiers that must train and be saved with the adapter.
   - Use `trainable_token_indices` for a small set of newly added token embeddings. Add tokens to the tokenizer and resize embeddings yourself before applying PEFT.

Minimal causal-LM LoRA pattern:

```python
from peft import LoraConfig, get_peft_model

peft_config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    use_rslora=True,
)
model = get_peft_model(base_model, peft_config)
```

## Variant selection

- `use_rslora=True`: use when increasing rank or when standard `alpha / r` scaling is unstable or underpowered.
- `use_dora=True`: adds a learnable magnitude branch in addition to LoRA direction; useful at low ranks, but adds overhead and currently targets linear and Conv2D layers. QDoRA can work with bitsandbytes, but DeepSpeed ZeRO-2 has reported issues.
- `init_lora_weights="pissa"` or `"pissa_niter_16"`: SVD/Fast-SVD initialization; use for faster convergence and quantization-error reduction. Full PiSSA can take minutes on large models; fast PiSSA trades exactness for speed.
- `init_lora_weights="corda"` with `CordaConfig`: use when you can run a preprocessing pass over task or knowledge-preservation data. Instruction-previewed mode favors task adaptation; knowledge-preserved mode favors retaining pretrained knowledge.
- `init_lora_weights="eva"` with `EvaConfig`: data-driven activation SVD initialization. Call `initialize_lora_eva_weights(peft_model, dataloader)` after wrapping. Use an accelerator and consider `low_cpu_mem_usage=True` in `get_peft_model`.
- `init_lora_weights="olora"`: QR-based initialization that mutates base weights before training; plan save/restore conversion carefully.
- `init_lora_weights="loftq"` with `LoftQConfig`: full LoftQ initialization that quantizes the backbone itself; do not pass an already quantized model.
- `init_lora_weights="lora_ga"` with `LoraGAConfig`: gradient-approximation initialization; run `preprocess_loraga` before training. Requires full-precision weights and does not support quantized models.
- `use_qalora=True`: QALoRA is currently implemented for GPTQ and linear layers. Ensure `module.in_features` is divisible by `qalora_group_size`.
- `alora_invocation_tokens=[...]`: aLoRA activates only during and after a tokenized invocation sequence for causal LM workflows and can reuse KV cache before invocation. Merging is not possible because adapter application is selective.
- `monteclora_config=MontecloraConfig(...)`: adds stochastic Monte Carlo sampling over LoRA adapters; tune sample count and regularization for calibration/stability tradeoffs.
- `velora_config=VeloraConfig(...)`: uses compressed activation storage in LoRA A backward pass to reduce training memory.
- `use_bdlora=BdLoraConfig(...)`: block-diagonal LoRA factors for serving-oriented communication reduction; keep A/B block target lists non-overlapping.
- `arrow_config=ArrowConfig(...)`: Arrow routing builds a router over compatible loaded LoRA adapters. The task/general adapters must have compatible target modules and rank.
- `AdaLoraConfig`: use AdaLoRA when the task calls for adaptive rank allocation during training; it has its own schedule parameters and supports bitsandbytes and GPTQ quantization.

See `references/lora-api.md` for parameter guidance and variant patterns.

## Quantized-base workflow

For 4-bit/8-bit bitsandbytes QLoRA-style training:

```python
import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
base_model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
)
base_model = prepare_model_for_kbit_training(base_model)
peft_config = LoraConfig(task_type="CAUSAL_LM", target_modules="all-linear", r=16, lora_alpha=32)
model = get_peft_model(base_model, peft_config)
```

Rules of thumb:

- Call `prepare_model_for_kbit_training` for k-bit bitsandbytes training before `get_peft_model`.
- Use `target_modules="all-linear"` for QLoRA-style language-model tuning and LoftQ coverage.
- Prefer NF4 for 4-bit bitsandbytes when combining with LoftQ.
- Use `dtype`/compute dtype deliberately: mismatched input and compute dtype can slow training or destabilize gradients.
- Save adapters separately for quantization formats that cannot merge LoRA into quantized weights.

See `references/quantization-workflows.md` for the backend matrix and LoftQ choice guide.

## LoftQ decision guide

- If the base model is not quantized yet and you can afford an initialization pass, use `LoraConfig(init_lora_weights="loftq", loftq_config=LoftQConfig(...))`. PEFT quantizes the backbone and initializes LoRA; do not pass a pre-quantized model.
- If the base model is already loaded with bitsandbytes 4-bit quantization, wrap it with ordinary LoRA first and then call `replace_lora_weights_loftq(peft_model)`. This only replaces LoRA weights in place, requires safetensors reference weights, supports only bitsandbytes 4-bit, and performs one LoftQ step.
- In either path, target as many linear layers as possible; layers without LoRA cannot receive LoftQ correction.

## Sanity script

Run the bundled sanity script without loading a model:

```bash
python skills/peft/sub-skills/lora-and-quantization/scripts/lora_config_sanity.py --check
python skills/peft/sub-skills/lora-and-quantization/scripts/lora_config_sanity.py --list-variants
```

The script constructs representative `LoraConfig` objects, reports optional dependency caveats, and catches configuration-time warnings/errors before a user spends time loading a large model.

## Failure triage

- `Please specify target_modules...`: use `target_modules="all-linear"`, explicit module suffixes, or `target_parameters` with `target_modules=[]` for parameter-only targets.
- LoftQ error with an already quantized model: switch from `init_lora_weights="loftq"` to ordinary LoRA plus `replace_lora_weights_loftq`.
- `loftq_config` ignored: set `init_lora_weights="loftq"`; otherwise remove `loftq_config`.
- QALoRA shape error: choose a `qalora_group_size` that divides each targeted linear layer input dimension, or narrow target modules.
- aLoRA appears inactive: ensure the tokenized invocation sequence is present in every input and the task is causal LM.
- Trainable tokens save too large: when only trainable tokens changed after resizing embeddings, consider `save_embedding_layers=False` during save.
- Missing quantization package: install the backend-specific extra or fall back to full precision, bitsandbytes, or a prequantized model supported by installed packages.

More issue patterns are in `references/troubleshooting.md`.
