# Local Inference Reference

Read this when OptiLLM is serving a local model rather than forwarding to an external provider.

## Activation

Set `OPTILLM_API_KEY` to any non-empty value to activate the local inference client:

```bash
export OPTILLM_API_KEY=optillm
optillm --model <huggingface-model-id>
```

This variable has high provider-selection precedence. If it is set accidentally, OptiLLM may try to download/load a local model instead of using OpenAI/Cerebras/Azure/LiteLLM.

## Model strings and adapters

Local inference accepts a base model id and optional LoRA adapter ids separated by `+`:

```text
base-model+adapter-1+adapter-2
```

The last adapter is active by default. Use request config to select an adapter:

```python
extra_body={"active_adapter": "adapter-1"}
```

Private models require a valid HuggingFace token. Blank token env vars are treated as unset by package import cleanup to avoid illegal empty authorization headers.

## Verified local API objects

Installed inspection confirmed these signatures:

```python
ModelConfig(
    base_model_id: str,
    adapter_ids: list[str] | None = None,
    batch_size: int = 32,
    max_cache_size: int = 5,
    quantization_bits: int = 4,
    device_preference: str | None = None,
    max_new_tokens: int = <factory>,
    do_sample: bool = True,
    top_p: float = 0.9,
    top_k: int = 50,
    temperature: float = 0.7,
    num_return_sequences: int = 1,
    repetition_penalty: float = 1.0,
    pad_token_id: int | None = None,
    logprobs: bool = False,
    use_memory_efficient_attention: bool = True,
    enable_prompt_caching: bool = True,
    dynamic_temperature: bool = False,
)
InferenceClient()
ChatCompletion(response_dict: dict)
```

`InferenceClient` caches pipelines by model/adapters. `ChatCompletion` wraps local responses in OpenAI-compatible objects and supports `model_dump()`.

## Request knobs

- `max_tokens` / `max_completion_tokens`: generation bound; important for tiny models that ramble.
- `logprobs` and `top_logprobs`: local inference can calculate top token logprobs.
- `active_adapter`: choose loaded LoRA adapter.
- `decoding`: select local decoding method when supported.
- Sampling fields: `temperature`, `top_p`, `top_k`, `repetition_penalty`.

`OPTILLM_MAX_TOKENS` controls the default max-new-token fallback used by local inference.

## Reasoning token accounting

OptiLLM counts tokens inside `<think>...</think>` sections and returns the estimate at:

```python
response.usage.completion_tokens_details.reasoning_tokens
```

If a `<think>` tag is truncated without a closing tag, the fallback counter still counts the open thinking content.

## Batching and caching

Local inference includes pipeline caching, prompt caching, and request batching infrastructure. Batch mode at the server layer is compatibility-checked and fail-fast. Do not assume every local model path benefits from true tensor batching; verify model-specific behavior before claiming throughput improvements.
