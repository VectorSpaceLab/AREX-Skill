---
name: model-reconstruction
description: "Guide Chinese-LLaMA-Alpaca asset selection, checksum validation,
  tokenizer extension, and LoRA reconstruction into PTH or Hugging Face model
  formats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Reconstruction Router

Use this sub-skill when a user needs to prepare Chinese-LLaMA-Alpaca model assets, merge Chinese LoRA adapters with legally obtained original LLaMA weights, extend tokenizers, choose PTH versus Hugging Face output, or debug reconstruction failures. The commands below assume the current working directory is this sub-skill directory.

The repository releases Chinese LLaMA/Alpaca **LoRA adapters and tokenizers**, not original full LLaMA weights. Do not imply the skill can supply original LLaMA weights or bypass license restrictions. Real reconstruction is large and should run only after the user confirms asset paths, disk/RAM budget, output format, and license constraints.

## Fast Route

1. **Confirm assets and model family.** Read [`references/model-assets.md`](references/model-assets.md) for original LLaMA, Chinese LLaMA, Chinese Alpaca, Plus/Pro, tokenizer, and multi-LoRA compatibility.
2. **Verify downloads before merging.** Use the root helper `../../scripts/verify_sha256.py` with checksums from [`references/checksums.md`](references/checksums.md).
3. **Choose the conversion path.** Use [`references/reconstruction-workflows.md`](references/reconstruction-workflows.md):
   - standard merge: `python scripts/merge_llama_with_chinese_lora.py ...`
   - low-memory or ordered multi-LoRA merge: `python scripts/merge_llama_with_chinese_lora_low_mem.py ...`
   - tokenizer extension: `python scripts/merge_tokenizers.py ...`
4. **Use bundled scripts only.** The copied scripts in [`scripts/`](scripts/) replace the source checkout scripts for runtime use.
5. **Troubleshoot before retrying.** Read [`references/troubleshooting.md`](references/troubleshooting.md) for tokenizer/vocab mismatch, PEFT version, RAM/disk, shard, and checksum problems.

## Bundled Runtime Files

- [`scripts/merge_llama_with_chinese_lora.py`](scripts/merge_llama_with_chinese_lora.py): standard LoRA merge to `pth` or Hugging Face format.
- [`scripts/merge_llama_with_chinese_lora_low_mem.py`](scripts/merge_llama_with_chinese_lora_low_mem.py): low-memory merge with ordered comma-separated LoRA paths.
- [`scripts/merge_tokenizers.py`](scripts/merge_tokenizers.py): Chinese tokenizer vocabulary extension; defaults to bundled [`scripts/chinese_sp.model`](scripts/chinese_sp.model).
- [`references/checksums.md`](references/checksums.md): distilled SHA256 table and verification workflow.

## Scope Boundaries

- Route inference, Gradio, FastAPI, OpenAI-compatible API, and LangChain prompts to `../inference-deployment/` after a merged or loadable model exists.
- Route new LoRA training or SFT data preparation to `../training-finetuning/`.
- Route C-Eval and example benchmark interpretation to `../evaluation-benchmarks/`.
- Do not run model reconstruction from a vague request. Ask for base model path, LoRA path(s), tokenizer expectations, output type, output directory, and available memory/disk first.
