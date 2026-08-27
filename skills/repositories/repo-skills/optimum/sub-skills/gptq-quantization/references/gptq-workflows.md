# GPTQ workflows for Optimum

This reference distills Optimum's GPT-QModel integration into operating steps for future agents. It is self-contained: use the installed package APIs and the bundled probe, not the original repository checkout.

## 1. Decide whether GPTQ is the right workflow

Use Optimum GPTQ when the user wants post-training GPTQ quantization or quantized loading for text causal language models through `optimum.gptq`.

Do not use this workflow for:

- ONNX Runtime, OpenVINO, Intel Neural Compressor, or other partner-package quantization/export flows.
- General quantization theory beyond what is needed to choose parameters.
- Non-text vision, speech, or multimodal models; this Optimum GPTQ integration is text-only.

## 2. Gate expensive work

Run the safe probe before any heavy action:

```bash
python scripts/gptq_availability_probe.py --json
```

For a hard preflight that should fail when full GPTQ dependencies are absent:

```bash
python scripts/gptq_availability_probe.py --strict
```

Interpretation:

- `optimum.gptq` import works: the Optimum GPTQ wrapper is importable.
- `gptqmodel>=7.0.0` works: `GPTQQuantizer` construction and quantized load can use GPT-QModel classes.
- `accelerate` works: `load_quantized_model` can dispatch quantized weights.
- `torch.cuda.available` or another GPT-QModel-supported accelerator works: full quantization/inference may be feasible. CPU-only probes are partial and do not validate kernels.

Before quantization, also obtain user approval for model/tokenizer downloads, calibration dataset access, GPU time, checkpoint write location, and acceptable quality checks.

## 3. Install/runtime requirements

Minimum practical full workflow requirements:

- Optimum with `optimum.gptq` available.
- `gptqmodel>=7.0.0`; older versions are rejected by Optimum's import utilities.
- `accelerate` for `load_quantized_model` dispatch.
- A compatible Transformers version for the selected model family.
- CUDA or another accelerator supported by the installed GPT-QModel backend for full quantization and fast inference.
- A text `AutoModelForCausalLM`-style model loaded as `torch.float16` for quantization.

Do not claim full GPTQ verification when only imports or CPU configuration checks passed.

## 4. Standard quantize-save-load flow

Only run this kind of workflow after the gate above is satisfied and the user approved downloads/GPU use.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.gptq import GPTQQuantizer, load_quantized_model

model_id = "facebook/opt-125m"  # example; may download unless cached
save_dir = "./gptq-model"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto",  # avoid disk entries for quantization
)

quantizer = GPTQQuantizer(
    bits=4,
    dataset=["Short representative calibration text."],
    group_size=128,
    desc_act=False,
    act_group_aware=True,
    sym=True,
)
quantized_model = quantizer.quantize_model(model, tokenizer)
quantizer.save(quantized_model, save_dir)
```

Loading a saved directory into an empty model uses Accelerate dispatch:

```python
import torch
from accelerate import init_empty_weights
from transformers import AutoConfig, AutoModelForCausalLM
from optimum.gptq import load_quantized_model

with init_empty_weights():
    empty_model = AutoModelForCausalLM.from_config(
        AutoConfig.from_pretrained(save_dir),
        torch_dtype=torch.float16,
    )
empty_model.tie_weights()

quantized_model = load_quantized_model(
    empty_model,
    save_folder=save_dir,
    device_map="auto",
    backend="auto",  # default; usually keep automatic kernel selection
)
```

Expected saved directory contents include model weights, `config.json` for Transformers models, and `quantize_config.json` for the GPTQ quantizer settings. If the user also needs tokenizer assets, save the tokenizer separately with `tokenizer.save_pretrained(save_dir)`.

## 5. Calibration dataset choices

`GPTQQuantizer.dataset` accepts:

- A list of raw text strings; Optimum tokenizes them with the provided tokenizer.
- A list of already tokenized dictionaries with `input_ids` and `attention_mask`.
- One of the built-in GPTQ paper dataset names: `"wikitext2"`, `"c4"`, or `"c4-new"`.

Prefer a small representative local list or pre-tokenized examples for controlled/offline work. The built-in dataset names require the `datasets` package and dataset access, and may download data.

If `batch_size > 1`, set `pad_token_id`; otherwise `prepare_dataset` raises an error because it cannot pad batched examples safely.

## 6. Custom causal language models

Automatic block and sequence-length inference is best-effort. Optimum recognizes common block paths such as:

- `transformer.h`
- `model.decoder.layers`
- `gpt_neox.layers`
- `model.layers`
- `model.language_model.layers`
- `h`
- `decoder.layers`
- `layers`

For custom models, inspect the module tree and provide the values explicitly:

```python
for name, _module in model.named_modules():
    if "layers" in name or "blocks" in name:
        print(name)

quantizer = GPTQQuantizer(
    bits=4,
    dataset=calibration_examples,
    model_seqlen=4096,
    block_name_to_quantize="transformer.blocks",
    module_name_preceding_first_block=["embed_tokens", "rotary_emb"],
    modules_in_block_to_quantize=[
        ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj"],
        ["self_attn.o_proj"],
        ["mlp.up_proj", "mlp.gate_proj"],
        ["mlp.down_proj"],
    ],
)
```

Notes for custom models:

- `block_name_to_quantize` must point to the module list containing Transformer blocks.
- `module_name_preceding_first_block` lists modules that must run before the first block during calibration.
- `modules_in_block_to_quantize` names are relative to each block and are quantized sequentially by inner list.
- If `model_seqlen` is missing, Optimum reads common config fields and otherwise falls back to `2048`; set it manually when that fallback is wrong.
- Custom save/load may need `block_name_to_quantize` preserved in `quantize_config.json` because Optimum's default serialized config omits some runtime-only constructor fields.

## 7. Selective layer quantization

Use `modules_in_block_to_quantize` to restrict quantization to selected linear layers or to enforce quantization ordering. Example from a BLOOM-like block:

```python
modules_in_block_to_quantize = [
    ["self_attention.query_key_value"],
    ["mlp.dense_h_to_4h"],
    ["mlp.dense_4h_to_h"],
]
```

Be precise: bad names can cause lookup failures during quantization or leave layers unconverted during load/convert steps. Derive names from `block.named_modules()`.

## 8. Format and backend guidance

`format="gptq"` is the default serialization-facing format and is used for broad checkpoint compatibility. During quantization, Optimum may use GPT-QModel's newer internal format and convert back during save for compatibility.

`backend="auto"` is the loading default and is normally the safest choice. Use an explicit backend only when all of the following are true:

1. The installed GPT-QModel version supports that backend name.
2. The selected hardware supports the backend.
3. The user has a concrete reason to override automatic kernel selection.

If backend selection fails, retry with `backend="auto"` before changing quantization parameters.

## 9. Disk offload rule

GPTQ quantization rejects a model `hf_device_map` containing `"disk"` with `ValueError: disk offload is not supported with GPTQ quantization`. Rebalance `max_memory`, reduce model size, use more GPU memory, or avoid quantizing that checkpoint in the current environment. CPU offload may exist in Accelerate, but it is not a substitute for disk offload and is not a proof of fast quantization.
