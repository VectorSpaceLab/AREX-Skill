# Chat Templates and Thinking Tokens

Chat templates let the harness format ordinary task prompts as conversations before sending them to chat-tuned models. Thinking-token arguments strip reasoning traces from generated outputs before metrics are computed.

## CLI Flags and Model Args

| Setting | Where | Meaning |
| --- | --- | --- |
| `--apply_chat_template` | CLI/config | Render prompts through the selected model's chat template. Can be boolean or a named template string. |
| `--fewshot_as_multiturn` | CLI/config | Format few-shot examples as multi-turn conversation. It is auto-enabled when `--apply_chat_template` is set unless explicitly disabled. |
| `--system_instruction` | CLI/config | Add a system message/instruction to chat-formatted prompts. |
| `enable_thinking=True` | `--model_args` | Ask the tokenizer/template to enable reasoning mode for supported models. |
| `think_end_token=...` | `--model_args` | Delimiter used to discard text up to and including the last thinking marker. Required with `enable_thinking=True`. |

## Backend Support Requirements

A backend must implement these methods/properties to support chat template flags:

- `tokenizer_name` for request-cache fingerprinting.
- `chat_template(chat_template=False)` to return the selected template string for result reproducibility.
- `apply_chat_template(chat_history, add_generation_prompt=True)` to render messages.

If a backend does not implement chat templating, the base `LM` raises `NotImplementedError` when chat template features are used.

## Chat Template Effects on Scoring

When `apply_chat_template=True`, the harness changes likelihood/multiple-choice delimiter behavior so the target delimiter is empty instead of the default whitespace. This prevents an extra space from being inserted between the chat template's assistant prefix and the answer text.

This means answer formatting can change. For closed chat models and generative tasks, use a small debug run with sample logging or write-out options from the evaluation-runs sub-skill before trusting final metrics.

## Thinking Model Rules

For Qwen3, DeepSeek-R1-style, or other reasoning models:

```bash
lm-eval run --model vllm \
  --model_args pretrained=Qwen/Qwen3-32B,enable_thinking=True,think_end_token="</think>" \
  --tasks gsm8k --apply_chat_template
```

With `hf`, `think_end_token` may be a string or integer token ID:

```bash
lm-eval run --model hf \
  --model_args pretrained=Qwen/Qwen3-32B,enable_thinking=True,think_end_token=200008 \
  --tasks gsm8k --apply_chat_template
```

With `vllm` and `sglang`, `think_end_token` must be a string delimiter such as `</think>`.

Do not use `enable_thinking=True` on loglikelihood or multiple-choice tasks. Current `hf` and `vllm` tests assert that loglikelihood raises a clear error when thinking mode is enabled, because scoring fixed continuations is incompatible with stripping generated reasoning traces.

## Endpoint Selection With Chat Formatting

A chat-tuned model does not always require a chat-completion endpoint.

- For generative tasks, chat-completion endpoints (`local-chat-completions`, `openai-chat-completions`, Anthropic chat, LiteLLM chat) are fine if the task only needs generated text.
- For likelihood tasks, prefer a completions endpoint that exposes logprobs, then apply chat formatting with `--apply_chat_template` if the tokenizer/template supports it.
- For local OpenAI-compatible servers, use `/v1/completions` with `local-completions` for likelihood tasks and `/v1/chat/completions` with `local-chat-completions` for generation-only tasks.

## Common Patterns

Hugging Face chat model with default template:

```bash
lm-eval run --model hf \
  --model_args pretrained=meta-llama/Meta-Llama-3-8B-Instruct,dtype=float16 \
  --tasks gsm8k --apply_chat_template
```

Named chat template if the backend exposes multiple templates:

```bash
lm-eval run --model hf \
  --model_args pretrained=my-org/my-model \
  --tasks gsm8k --apply_chat_template my-template-name
```

Chat formatted few-shot examples as single-turn prompts:

```bash
lm-eval run --model hf \
  --model_args pretrained=my-org/my-chat-model \
  --tasks gsm8k --apply_chat_template --fewshot_as_multiturn false
```

## Troubleshooting Chat Templates

- `NotImplementedError` about `apply_chat_template`: the selected backend does not implement chat template support; use another backend or implement the methods described above.
- Tokenizer has no chat template: pass a supported model/tokenizer, choose a named template if available, or implement rendering in the custom backend.
- Answer extraction fails on closed chat models: run a small limit and adjust the task prompt/extraction in task-authoring, or add a system instruction if the backend supports it.
- Thinking output still appears in samples: confirm `think_end_token` exactly matches the tokenizer's closing thinking delimiter and is the correct type for the backend.
- String token appears in normal text: with `hf`, prefer the integer token ID form when possible.
