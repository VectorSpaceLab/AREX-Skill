# API Model Backends

Use API backends for hosted commercial models, local OpenAI-compatible servers, and custom HTTP model services. Install the narrow API extra first:

```bash
pip install "lm_eval[api]"
```

LiteLLM has its own extra:

```bash
pip install "lm_eval[litellm]"
```

## Completion vs Chat Completion

This distinction is usually the root cause of API backend failures.

| Need | Prefer | Avoid | Why |
| --- | --- | --- | --- |
| Multiple-choice, MMLU-style, `loglikelihood`, or perplexity | `local-completions` or `openai-completions` | `local-chat-completions`, `openai-chat-completions`, Anthropic chat, LiteLLM chat | Chat-completion endpoints do not expose the token logprobs required by the harness scoring path |
| Pure generation or instruction following | Chat or completion endpoint | None, if task output type is generative | Generation only needs `generate_until` and parsed text |
| OpenAI-compatible local server with logits/logprobs | `local-completions` | `local-chat-completions` | Completion endpoint can send prompts, logprobs, and echo-style scoring |
| Instruct-tuned model on a loglikelihood task | `local-completions` plus `--apply_chat_template` if tokenizer/template supports it | Chat endpoint | Completion API can preserve logprob access while prompts are rendered in chat format |

Difficult case: if the user asks to evaluate a local OpenAI-compatible chat endpoint on `lambada_openai`, explain that `lambada_openai` uses likelihood scoring. Use a completions endpoint with logprobs if the server supports it, or switch to a generative task.

## Built-In API Aliases

| Alias | Credential | Notes |
| --- | --- | --- |
| `local-completions` | Optional `auth_token` or header depending on server | OpenAI completions payload; can use `tokenizer_backend=auto`, `huggingface`, `tiktoken`, `remote`, or `None` |
| `local-chat-completions` | Optional server auth | OpenAI chat-completions payload; generation only; batch size forced to 1 |
| `openai-completions` | `OPENAI_API_KEY` | Defaults to OpenAI `/v1/completions`, tiktoken tokenizer |
| `openai-chat-completions` | `OPENAI_API_KEY` | Requires `--apply_chat_template`; generation only |
| `anthropic-chat`, `anthropic-chat-completions` | `ANTHROPIC_API_KEY` | Generation only |
| `litellm`, `litellm-chat`, `litellm-chat-completions` | Provider-specific environment variables | LiteLLM gateway to many providers; generation only in current built-in class |
| `textsynth` | Provider token | Completion API style; check provider capabilities |
| `watsonx_llm` | IBM Watsonx credentials | Install `lm_eval[ibm_watsonx_ai]` |

## `TemplateAPI` Constructor Arguments

`TemplateAPI` handles batching, retrying, caching, tokenization, request payload dispatch, and parsing hooks. Important model args include:

| Argument | Purpose |
| --- | --- |
| `model` or `pretrained` | Remote model identifier; `model` takes precedence |
| `base_url` | Endpoint URL, such as `http://127.0.0.1:8000/v1/completions` |
| `tokenizer` | Separate tokenizer name/path when the API model name is not a tokenizer ID |
| `tokenizer_backend` | `huggingface`, `tiktoken`, `remote`, `None`, or `auto` for `local-completions` |
| `tokenized_requests` | Send token IDs when true; decode back to text when false |
| `num_concurrent` | Concurrent HTTP requests; keep low for fragile local servers |
| `batch_size` | Batched requests; API models default to 1 and warn on unsupported auto batching |
| `max_retries` | Retry count for transient HTTP failures |
| `timeout` | Request timeout in seconds |
| `verify_certificate`, `ca_cert_path` | TLS verification controls for HTTPS endpoints |
| `auth_token`, `header` | Auth for local or custom APIs; avoid embedding secrets in saved configs |
| `max_length`, `max_gen_toks`, `seed` | Token length/generation defaults |

## Safe Command Patterns

OpenAI completions on a likelihood task:

```bash
export OPENAI_API_KEY=...
lm-eval run --model openai-completions \
  --model_args model=davinci-002 \
  --tasks lambada_openai
```

Local completions endpoint with Hugging Face tokenizer and string requests:

```bash
lm-eval run --model local-completions \
  --model_args model=facebook/opt-125m,base_url=http://127.0.0.1:8000/v1/completions,tokenizer=facebook/opt-125m,tokenizer_backend=huggingface,tokenized_requests=False,num_concurrent=1,max_retries=3 \
  --tasks lambada_openai
```

Local chat endpoint for a generation task:

```bash
lm-eval run --model local-chat-completions \
  --model_args model=my-chat-model,base_url=http://127.0.0.1:8000/v1/chat/completions,num_concurrent=1,max_retries=3 \
  --tasks gsm8k --apply_chat_template
```

LiteLLM chat generation:

```bash
export OPENAI_API_KEY=...
lm-eval run --model litellm-chat-completions \
  --model_args model=gpt-4o-mini \
  --tasks gsm8k --apply_chat_template
```

## Implementing a Custom API Backend

Subclass `lm_eval.models.api_models.TemplateAPI` when adapting a non-OpenAI HTTP service.

Required implementation points:

1. `_create_payload(messages, generate=False, gen_kwargs=None, seed=1234, eos=None, **kwargs)` to build the HTTP JSON body.
2. `parse_logprobs(outputs, tokens=None, ctxlens=None, **kwargs)` if the API supports likelihood scoring.
3. `parse_generations(outputs, **kwargs)` to return generated strings in request order.
4. Optional `api_key` and `header` properties for provider authentication.

Register with `@register_model("my-api")` and expose through the model registry mapping if contributing inside the package.

## Diagnostics

- `ModuleNotFoundError` mentioning `aiohttp`, `requests`, `tenacity`, or `tqdm`: install `lm_eval[api]`.
- `tiktoken` missing for OpenAI completions: install `lm_eval[api]`; for non-OpenAI models prefer `tokenizer_backend=huggingface,tokenizer=<hf-tokenizer-id>`.
- `API key not found`: set the provider environment variable, such as `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.
- HTTP 404/405: base URL likely points at chat endpoint while using completions backend, or vice versa.
- `Loglikelihood is not supported for chat completions`: switch to `local-completions`/`openai-completions` or choose a generative task.
- Garbled scoring on instruct models: use `--apply_chat_template` with a completion endpoint and inspect a small `--limit` run.
