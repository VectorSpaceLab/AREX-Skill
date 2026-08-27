# Baichuan2 Model Overview

Use this reference before choosing a Baichuan2 checkpoint for inference, deployment, or fine-tuning.

## Released model families

| Family | Model id pattern | Best fit | Route |
| --- | --- | --- | --- |
| 7B Base | `baichuan-inc/Baichuan2-7B-Base` | Continuation/generation tasks, supervised fine-tuning starting point, lower memory than 13B. | `fine-tuning` for training; `inference` for Base generation. |
| 7B Chat | `baichuan-inc/Baichuan2-7B-Chat` | Assistant-style chat with lower memory than 13B. | `inference`; `deployment` for quantized variants. |
| 7B Chat 4-bit | `baichuan-inc/Baichuan2-7B-Chat-4bits` | Memory-constrained chat deployment. | `deployment`. |
| 13B Base | `baichuan-inc/Baichuan2-13B-Base` | Stronger continuation/generation, heavier than 7B. | `inference` for Base generation; training only with adequate resources. |
| 13B Chat | `baichuan-inc/Baichuan2-13B-Chat` | Default high-quality Chat demo/API checkpoint. | `inference`. |
| 13B Chat 4-bit | `baichuan-inc/Baichuan2-13B-Chat-4bits` | Reduced-memory 13B Chat deployment when a published 4-bit checkpoint is acceptable. | `deployment`. |

## Choosing by task

- Use **Chat** checkpoints for assistant-style prompts, the CLI demo, Streamlit demo, and OpenAI-compatible API helper.
- Use **Base** checkpoints for plain continuation/generation and as the default full fine-tuning starting point.
- Use **7B** when memory or runtime budget matters.
- Use **13B** when quality is more important and the host has sufficient memory.
- Use **4-bit Chat** checkpoints or BitsAndBytes quantization when deployment memory is the limiting constraint.
- Use CPU float32 loading only when GPU is unavailable and slow inference is acceptable.

## Model-code assumptions

Baichuan2 Hugging Face checkpoints rely on remote model code. Runtime examples normally set:

```python
trust_remote_code=True
use_fast=False  # tokenizer
```

For Chat checkpoints, after loading the tokenizer and model, use:

```python
response = model.chat(tokenizer, messages)
```

For Base checkpoints, tokenize a prompt and call `model.generate(...)`; do not expect `model.chat(...)` or the Chat demo wrappers to be appropriate.

## Benchmark and research context

The README reports broad Chinese, English, multilingual, law/medicine, math, and code benchmark tables, and states Baichuan2 was trained on 2.6 trillion tokens. This skill does not reproduce benchmark workflows; use the model overview only for task routing and model-family selection.
