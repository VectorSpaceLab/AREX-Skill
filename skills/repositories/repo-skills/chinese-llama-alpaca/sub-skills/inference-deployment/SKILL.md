---
name: inference-deployment
description: "Guide Chinese-LLaMA-Alpaca Hugging Face inference, Gradio chat,
  OpenAI-compatible API serving, and optional LangChain integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Deployment Router

Use this sub-skill when a user has, or is preparing, Chinese-LLaMA-Alpaca model assets for local generation, batch prediction, interactive instruction mode, Gradio chat, an OpenAI-compatible FastAPI server, embeddings, or LangChain QA/summarization. The commands below assume the current working directory is this sub-skill directory.

Do not launch a long-running server, download model weights, or load a large 7B+ model unless the user confirms model paths, backend use, port/network exposure, and runtime budget. If the user only has LoRA adapters and no loadable base/merged model, route first to `../model-reconstruction/`.

## Fast Route

1. **Pick the model family.** Chinese LLaMA is base/continuation-oriented; Chinese Alpaca is instruction/chat-oriented. Use [`references/hf-inference.md`](references/hf-inference.md) for prompt and flag details.
2. **Run batch or interactive HF inference** with [`scripts/inference_hf.py`](scripts/inference_hf.py) when a HF model/base+LoRA path is available.
3. **Use Gradio or API serving only with explicit launch approval.** See [`references/gradio-and-api-server.md`](references/gradio-and-api-server.md) before running [`scripts/gradio_demo.py`](scripts/gradio_demo.py) or [`scripts/openai_api_server.py`](scripts/openai_api_server.py).
4. **Use LangChain guidance for optional app demos.** See [`references/langchain-integrations.md`](references/langchain-integrations.md); these scripts require extra packages and model/embedding paths.
5. **Debug failures with exact symptoms.** Use [`references/troubleshooting.md`](references/troubleshooting.md) for tokenizer mismatch, CPU/GPU, 8-bit, NTK, xFormers, Gradio, FastAPI request schema, and optional dependency errors.

## Bundled Runtime Files

- [`scripts/inference_hf.py`](scripts/inference_hf.py): HF batch and single-turn interactive inference.
- [`scripts/gradio_demo.py`](scripts/gradio_demo.py): Gradio chat UI.
- [`scripts/openai_api_server.py`](scripts/openai_api_server.py) and [`scripts/openai_api_protocol.py`](scripts/openai_api_protocol.py): OpenAI-compatible completions/chat/embeddings server and schemas.
- [`scripts/patches.py`](scripts/patches.py): local attention and NTK scaling patch module used by inference/server scripts.
- [`scripts/langchain_qa.py`](scripts/langchain_qa.py), [`scripts/langchain_sum.py`](scripts/langchain_sum.py), and [`scripts/doc.txt`](scripts/doc.txt): optional LangChain examples.

## Scope Boundaries

- Model conversion, tokenizer extension, SHA256 checks, and LoRA merging belong to `../model-reconstruction/`.
- Training or SFT of new adapters belongs to `../training-finetuning/`.
- C-Eval scoring and example benchmark interpretation belong to `../evaluation-benchmarks/`.
- This sub-skill can plan CPU-only checks, but CPU generation for 7B+ models is often very slow and is not a substitute for GPU performance validation.
