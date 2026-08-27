---
name: inference-chat
description: "Use LitGPT for local text generation, chat, and Python API
  inference from ready checkpoints, including prompt styles, sampling,
  quantization, and multi-device generation routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LitGPT Inference And Chat

Use this sub-skill when the user wants to generate text locally with LitGPT, chat interactively, or write Python API inference code against a ready checkpoint. It covers `litgpt generate`, `litgpt chat`, specialized generation commands, and `litgpt.LLM` / `litgpt.api.LLM` workflows.

## Route First

- Use this sub-skill for local generation, chat REPLs, API `LLM.load`, `LLM.generate`, `LLM.distribute`, prompt-style selection, sampling settings, quantization for inference, and sequential/tensor-parallel generation.
- Route checkpoint download, HF conversion, LitGPT checkpoint validation, `model_config.yaml`, tokenizer placement, and LoRA merge planning to `../checkpoint-conversion/` before generation.
- Route finetuning/pretraining output creation and adapter checkpoint ownership to `../training-data/`; return here only to generate from the produced weights.
- Route HTTP APIs, LitServe, OpenAI-compatible serving, and LM Evaluation Harness tasks to `../evaluation-serving/`.

## Fast Start

1. Confirm the checkpoint is already local and LitGPT-formatted, or route to `../checkpoint-conversion/`.
2. Run the bundled preflight before loading weights:

   ```bash
   python sub-skills/inference-chat/scripts/check_inference_inputs.py \
     --checkpoint-dir checkpoints/example-model \
     --prompt "What food do llamas eat?" \
     --max-new-tokens 50 \
     --top-k 50 \
     --top-p 1.0 \
     --temperature 0.8
   ```

3. For one-shot local text generation, use `litgpt generate CHECKPOINT_DIR --prompt "..."`.
4. For interactive local chat, use `litgpt chat CHECKPOINT_DIR`; add `--multiline true` for multi-line user prompts.
5. For Python code, prefer local paths for offline work:

   ```python
   from litgpt import LLM

   llm = LLM.load("checkpoints/example-model")
   text = llm.generate("What do llamas eat?", max_new_tokens=80, top_k=1)
   print(text)
   ```

## References

- `references/cli-reference.md`: command matrix for `generate`, `chat`, adapter/full generation, sequential, speculative, and tensor-parallel routes.
- `references/api-reference.md`: Python API signatures, offline loading patterns, streaming, benchmarking, and distribution strategies.
- `references/workflows.md`: end-to-end local, chat, prompt-style, quantized, adapter, and multi-device workflows.
- `references/troubleshooting.md`: common failures for checkpoint layout, sampling, tokenizer/prompt styles, quantization, hardware, LoRA/adapters, and accidental network access.

## Safety Notes

- The bundled checker never loads model weights, downloads checkpoints, starts servers, trains models, or writes outside normal Python bytecode caches.
- `LLM.load(model_name, init="pretrained")` may download if `model_name` is not a local checkpoint path. For offline operation, use an existing local checkpoint path or pass `init="random"` with an explicit local `tokenizer_dir` only when random weights are intentional.
- `bnb.*` inference quantization requires the optional `bitsandbytes` package and CUDA/Linux-compatible runtime; do not assume it works in CPU-only environments.
