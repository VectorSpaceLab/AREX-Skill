# Model overview

## Model families

| Family | Sizes in this repo | Primary use | Notes |
| --- | --- | --- | --- |
| Chinese-LLaMA-2 | 1.3B, 7B, 13B | Base-model continuation and downstream adaptation | Not a chat model; prompt wrapping is optional unless a downstream task expects it. |
| Chinese-Alpaca-2 | 1.3B, 7B, 13B | Instruction-following and chat-style generation | Uses the Alpaca-2 system prompt and Llama-2-chat-style formatting. |
| Long-context LLaMA/Alpaca variants | 7B, 13B, plus 64K on 7B | Long-document or long-turn generation | Use NTK/attention helpers and choose a long-context checkpoint. |
| RLHF variants | 1.3B, 7B | Preference-aligned chat | Same general usage shape as the standard Alpaca-2 chat models. |

## Context and compatibility guidance

| Surface | Typical compatibility | Notes |
| --- | --- | --- |
| Transformers inference | CPU or GPU | The repo's native scripts support CPU-only mode for basic inference, but optional acceleration features are GPU-oriented. |
| llama.cpp | CPU or GPU | Requires an external llama.cpp binary and the appropriate GGUF model. |
| OpenAI-style FastAPI server | CPU or GPU | The non-vLLM server can run on CPU if the model fits; LoRA and quantization options depend on the branch you choose. |
| vLLM server | GPU only | The optional vLLM branch is not part of the minimum inspection env. It does not support the same LoRA/quantization combinations as the non-vLLM server. |
| LangChain/privateGPT examples | CPU or GPU depending on the downstream stack | Treat these as integration notes, not as a bundled repo-maintained runtime stack. |

## Prompt and token behavior

- The repository uses a single simplified default system prompt for Alpaca-2.
- The bundled tokenizer files are project-specific and should not be mixed with first-generation Chinese-LLaMA/Alpaca tokenizers.
- Scripts that load a base model and tokenizer may resize embeddings automatically when the vocabulary size does not match.

## Practical model selection

- Use a base Chinese-LLaMA-2 checkpoint when the task is continuation or low-level text generation.
- Use a Chinese-Alpaca-2 checkpoint when the task is chat, instruction following, or a user-facing assistant flow.
- Use a long-context checkpoint when the task is document-heavy or needs 16K/64K context.
- Use an RLHF checkpoint when value alignment matters more than raw continuation style.
