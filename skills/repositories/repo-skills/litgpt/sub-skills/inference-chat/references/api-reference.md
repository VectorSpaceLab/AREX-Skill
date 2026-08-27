# LitGPT Python API Reference For Inference

This reference covers the verified `LLM` API surface for local generation and chat-like use. It is intended for agents writing user code without reopening LitGPT source files.

## Imports

Both imports are used in LitGPT examples:

```python
from litgpt import LLM
# or
from litgpt.api import LLM
```

## `LLM.load`

Verified signature:

```python
LLM.load(
    model: str,
    init: "pretrained" | "random" | None = "pretrained",
    tokenizer_dir=None,
    access_token=None,
    distribute="auto",
)
```

Behavior:

- `model` may be a local LitGPT checkpoint directory or a supported model identifier.
- `init="pretrained"` loads existing weights. If the string is not a local checkpoint path, LitGPT may download from the Hugging Face Hub.
- `init="random"` builds random weights from a supported model config name and requires a valid `tokenizer_dir` when no checkpoint directory is available.
- `tokenizer_dir` overrides tokenizer loading, useful when random initialization or a separate tokenizer location is intentional.
- `access_token` is only relevant for restricted remote model access; avoid it for offline workflows.
- `distribute="auto"` initializes the model immediately on one CUDA device when available, then MPS, then CPU. Use `distribute=None` to delay device placement and call `.distribute(...)` manually.

Offline-safe local loading:

```python
from litgpt import LLM

llm = LLM.load("checkpoints/example-model")
print(llm.generate("What do llamas eat?", max_new_tokens=60, top_k=1))
```

Offline-safe delayed distribution:

```python
from litgpt import LLM

llm = LLM.load("checkpoints/example-model", distribute=None)
llm.distribute(accelerator="cpu", devices=1, precision="32-true")
print(llm.generate("Summarize KV caches.", max_new_tokens=80))
```

Random-weight initialization is not a normal inference path; use it for tests or pretraining scaffolds only:

```python
llm = LLM.load("pythia-160m", init="random", tokenizer_dir="path/to/tokenizer")
```

If `init="random"` is combined with `distribute=None`, calling `.generate(...)` before `.trainer_setup()` or a supported `.distribute(...)` raises a model-not-initialized error. Multi-device `.distribute(generate_strategy=...)` does not support random-initialized `LLM` objects.

## `LLM.generate`

Verified signature:

```python
LLM.generate(
    prompt: str,
    sys_prompt: str | None = None,
    max_new_tokens: int = 50,
    temperature: float = 1.0,
    top_k: int | None = None,
    top_p: float = 1.0,
    return_as_token_ids: bool = False,
    stream: bool = False,
)
```

Behavior:

- `prompt` is first transformed by the active prompt style, then tokenized.
- `sys_prompt` is passed into prompt styles that support system prompts.
- `max_new_tokens` controls generated tokens, not including prompt tokens.
- `temperature=0` or `top_p=0` produces greedy argmax decoding.
- `top_p` must be in `[0, 1]`.
- `top_k=None` disables top-k filtering; `top_k=1` is near-greedy.
- `return_as_token_ids=True` returns a token tensor instead of decoded text.
- `stream=True` returns an iterator that yields token text pieces; LitGPT notes this path can currently be slower and use more memory than non-streaming generation.

Streaming example:

```python
result = llm.generate("Write one sentence about alpacas.", stream=True)
for piece in result:
    print(piece, end="", flush=True)
```

Token IDs example:

```python
token_ids = llm.generate("Hello", max_new_tokens=10, return_as_token_ids=True)
```

## `LLM.distribute`

Verified signature:

```python
LLM.distribute(
    accelerator="auto",
    devices="auto",
    precision=None,
    quantize=None,
    generate_strategy=None,
    fixed_kv_cache_size=None,
)
```

Behavior:

- `accelerator` accepts `"auto"`, `"cpu"`, `"gpu"`, `"cuda"`, or `"mps"`.
- With `accelerator="auto"`, LitGPT prefers CUDA, then MPS, then CPU.
- `devices="auto"` uses one device for ordinary generation and all available CUDA devices for `generate_strategy="sequential"` or `"tensor_parallel"`.
- Multiple devices require `generate_strategy="sequential"` or `"tensor_parallel"`.
- `generate_strategy="sequential"` partitions transformer blocks across CUDA devices and can run models that do not fit on one GPU, usually more slowly.
- `generate_strategy="tensor_parallel"` shards linear layers across CUDA devices and launches distributed workers; it requires CUDA/GPU and compatible model dimensions.
- `fixed_kv_cache_size` preallocates KV cache length. Use an integer to cap max generated context or `"max_model_supported"` for the model limit. Sequential generation defaults to a fixed max-model-supported cache.
- `quantize` supports `bnb.nf4`, `bnb.nf4-dq`, `bnb.fp4`, `bnb.fp4-dq`, and `bnb.int8` in the API. Bitsandbytes quantization cannot be combined with mixed precision.

Single GPU/CUDA example:

```python
llm = LLM.load("checkpoints/example-model", distribute=None)
llm.distribute(accelerator="cuda", devices=1, precision="bf16-true")
```

Sequential multi-GPU example:

```python
llm = LLM.load("checkpoints/large-model", distribute=None)
llm.distribute(
    accelerator="cuda",
    devices=4,
    generate_strategy="sequential",
    fixed_kv_cache_size=512,
)
print(llm.generate("Give two memory-saving tips.", max_new_tokens=128))
```

Tensor-parallel example. Place this in a Python script guarded by `if __name__ == "__main__":` rather than inside an interactive notebook:

```python
from litgpt import LLM

if __name__ == "__main__":
    llm = LLM.load("checkpoints/example-model", distribute=None)
    llm.distribute(accelerator="cuda", devices=4, generate_strategy="tensor_parallel")
    print(llm.generate("What is tensor parallelism?", top_k=1))
```

## Benchmarking

LitGPT exposes `.benchmark(...)` with the same generation arguments plus `num_iterations`. It returns generated text and a metrics dictionary. Discard the first iteration when comparing warm performance.

```python
text, metrics = llm.benchmark(num_iterations=5, prompt="What do llamas eat?", top_k=1)
```

Useful metrics include seconds to first token, seconds total, tokens generated, tokens/sec, and GPU memory allocated when CUDA is used.

## Prompt Styles And Tokenizers

`LLM.load` chooses the prompt style as follows:

1. If the checkpoint directory contains a bundled prompt style file, load it.
2. Otherwise derive a prompt style from `model_config.yaml`.

The tokenizer is loaded from `tokenizer_dir` when provided, otherwise from the checkpoint directory. A tokenizer mismatch can make generated output look malformed even when weights load successfully. For offline workflows, provide an explicit local `tokenizer_dir` only when it is intentionally different and compatible.

## Common API Exceptions To Recognize

- `ValueError: Invalid init option`: `init` must be `"pretrained"` or `"random"`.
- `ValueError: Provide a path to a tokenizer directory`: random initialization needs tokenizer files.
- `AttributeError: The model is not initialized yet`: call `.distribute(...)` or `.trainer_setup()` after `LLM.load(..., distribute=None)` before `.generate(...)`.
- `NotImplementedError: generate_strategy='...' is only supported for accelerator='cuda'|'gpu'`: sequential and tensor-parallel strategies require CUDA/GPU.
- `NotImplementedError: init='random' ... .distribute() currently only supports pretrained weights`: multi-device API distribution is for pretrained checkpoints.
- `ValueError: You selected more devices ... than available`: reduce `devices` or adjust visible GPUs.
- `ValueError: top_p must be in [0, 1]`: fix sampling options before loading large weights.
