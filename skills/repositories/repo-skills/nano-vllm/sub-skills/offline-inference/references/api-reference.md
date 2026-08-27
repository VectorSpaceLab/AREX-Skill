# Offline inference API reference

## Public objects

```python
from nanovllm import LLM, SamplingParams
```

`LLM` is a thin public subclass of the engine. Construction is:

```python
LLM(model: str, **kwargs)
```

Recognized keyword arguments are the fields of `Config`:

| Argument | Default | Operational meaning |
| --- | ---: | --- |
| `max_num_batched_tokens` | `16384` | Prefill token budget per scheduler step. |
| `max_num_seqs` | `512` | Maximum sequences scheduled together. |
| `max_model_len` | `4096` | Upper context length, clipped to the model config's positional limit. |
| `gpu_memory_utilization` | `0.9` | Fraction of total GPU memory used to size the KV cache. |
| `tensor_parallel_size` | `1` | Number of NCCL ranks/GPUs; must be 1–8 and divide model dimensions. |
| `enforce_eager` | `False` | Skip CUDA graph capture when true. Use true for first smoke tests. |
| `kvcache_block_size` | `256` | KV-cache block size; it must be a multiple of 256. |

The model argument must be an existing directory. The constructor reads its
Hugging Face config and tokenizer, creates a CUDA model runner, loads all
matching safetensors, warms up the model, and allocates a KV cache.

## SamplingParams

```python
SamplingParams(
    temperature: float = 1.0,
    max_tokens: int = 64,
    ignore_eos: bool = False,
)
```

The post-init assertion requires `temperature > 1e-10`; this implementation
uses stochastic sampling and does not permit a greedy temperature of zero.
`max_tokens` is the completion budget. `ignore_eos=True` lets generation
continue through the tokenizer's EOS id until the budget is reached.

## Generate

```python
llm.generate(
    prompts: list[str] | list[list[int]],
    sampling_params: SamplingParams | list[SamplingParams],
    use_tqdm: bool = True,
) -> list[dict[str, object]]
```

Although the source annotation says `list[str]`, the implementation returns a
list of dictionaries, one per prompt:

```python
{
    "text": "decoded completion text",
    "token_ids": [int, int, ...],
}
```

A string prompt is tokenized with the engine's fast `AutoTokenizer`. A token-id
prompt is passed through directly and must be non-empty. If one
`SamplingParams` object is supplied, it is reused for every prompt. If a list
is supplied, its position is paired with the corresponding prompt; validate
that lengths match before calling.

Results are collected by internal sequence id and sorted before decoding, so
request order is preserved. `use_tqdm=False` suppresses the progress bar and
is preferable for library/server logs.

## Lifecycle and constraints

The engine registers `exit()` with `atexit` and starts spawned processes for
ranks above zero. In a long-lived host call `llm.exit()` exactly once during
shutdown. Keep construction in a main guard. Do not construct an engine just
to inspect a model config: use the bundled contract checker in the internals
route or Transformers' config loader.
