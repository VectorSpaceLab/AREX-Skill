# Pipeline API Reference

This reference covers offline text inference with LMDeploy `0.13.0` package APIs. It intentionally omits server APIs, multimodal media details, quantization artifact creation, and backend extension internals.

## Entry Points

### `lmdeploy.pipeline(...)`

Use the factory exported from `lmdeploy.api`:

```python
from lmdeploy import pipeline

pipe = pipeline(
    model_path="org/model-or-local-path",
    backend_config=None,
    chat_template_config=None,
    log_level="WARNING",
    max_log_len=None,
    trust_remote_code=False,
)
```

Verified signature:

```text
pipeline(model_path: str,
         backend_config=None,
         chat_template_config=None,
         log_level='WARNING',
         max_log_len=None,
         trust_remote_code=False,
         speculative_config=None,
         **kwargs)
```

`model_path` may be a local model directory, a converted or quantized TurboMind model directory, an LMDeploy-quantized model repo id, or a Hugging Face model repo id. If a path does not exist locally, LMDeploy may resolve/download it through its model-loading utilities, so prefer a local path when the task must be fully offline.

`pipeline(...)` returns a `Pipeline` instance. Use `with pipeline(...) as pipe:` or call `pipe.close()` to release the internal event loop and engine resources.

### Backend Configs

Choose one config object and pass it as `backend_config`:

```python
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig

# TurboMind default backend for many supported text LLMs.
tm_config = TurbomindEngineConfig(
    dtype="auto",
    tp=1,
    session_len=None,
    max_batch_size=None,
    cache_max_entry_count=0.8,
    enable_prefix_caching=False,
)

# PyTorch backend, useful for PyTorch engine features such as LoRA adapters.
pt_config = PytorchEngineConfig(
    dtype="auto",
    tp=1,
    session_len=None,
    max_batch_size=None,
    cache_max_entry_count=0.8,
    adapters=None,
    enable_prefix_caching=False,
)
```

Common inference knobs:

| Knob | Applies to | Use |
| --- | --- | --- |
| `dtype` | both | `"auto"`, `"float16"`, or `"bfloat16"` weight/activation dtype selection. |
| `tp` | both | Tensor parallel GPU count. Keep `1` unless the model requires multiple devices or throughput benefits justify it. |
| `session_len` | both | Maximum session length; raise for long conversations if memory allows. |
| `max_batch_size` | both | Upper bound on concurrent batched requests; LMDeploy can infer a value when omitted. |
| `cache_max_entry_count` | both | Fraction of free GPU memory reserved for KV cache in modern LMDeploy; lower it to mitigate OOM. |
| `enable_prefix_caching` | both | Reuse prefix cache for repeated prompts; do not use with interactive `lmdeploy chat`. |
| `quant_policy` | both | KV-cache quant policy. TurboMind supports `0`, `4`, `8`, and TurboQuant; PyTorch also validates FP8 policies on supported devices. |
| `adapters` | PyTorch | Mapping of LoRA adapter name to path or repo id. Select with `adapter_name` during inference. |
| `device_type` | PyTorch | Accelerator type such as `"cuda"`, `"ascend"`, `"maca"`, or `"camb"` when supported by the install. |
| `model_format` | both | Weight format hint such as `"hf"`, `"awq"`, `"gptq"`, `"compressed-tensors"`, `"fp8"`, or `"mxfp4"` when auto-detection is not enough. |
| `download_dir` / `revision` | both | Control where remote models are resolved and which revision is used. |

For TurboMind, `cache_max_entry_count` can also be an integer block count. For PyTorch, validation requires `0 < cache_max_entry_count < 1`.

## `GenerationConfig`

Use `GenerationConfig` to control decoding and requested output payloads:

```python
from lmdeploy import GenerationConfig

gen_config = GenerationConfig(
    max_new_tokens=128,
    do_sample=True,
    top_p=0.9,
    top_k=40,
    temperature=0.7,
    stop_words=["</s>"],
)
```

Verified defaults and fields include:

| Field | Default | Notes |
| --- | --- | --- |
| `n` | `1` | Only one choice is supported by current engines. |
| `max_new_tokens` | `512` | Max generated tokens. Use `0` to return immediately with no generated tokens. |
| `do_sample` | `False` | Greedy decoding unless enabled. |
| `top_p` | `1.0` | Must be in `[0, 1]`. |
| `top_k` | `50` | Must be non-negative. |
| `min_p` | `0.0` | Must be in `[0, 1]`. |
| `temperature` | `0.8` | Must be in `[0, 2]`. |
| `repetition_penalty` | `1.0` | Penalizes repeated words/phrases. |
| `ignore_eos` | `False` | Continue past EOS when true. |
| `random_seed` | `None` | Sampling seed. |
| `stop_words` / `bad_words` | `None` | String lists converted through tokenizer lookup. |
| `stop_token_ids` / `bad_token_ids` | `None` | Token-id stop/ban lists. |
| `skip_special_tokens` | `True` | Detokenization behavior. |
| `spaces_between_special_tokens` | `True` | Slow-tokenizer special-token spacing behavior. |
| `logprobs` | `None` | Number of top logprobs per output token. |
| `response_format` | `None` | JSON-schema or regex-schema constrained generation payload. |
| `output_logits` | `None` | Set to `"generation"` or `"all"` when supported and memory allows. |
| `output_last_hidden_state` | `None` | Set to `"generation"` or `"all"` when supported and memory allows. |
| `include_stop_str_in_output` | `False` | Whether stop strings remain in decoded output. |
| `return_ppl` | `False` | Request prompt cross-entropy metadata in engine output; `Pipeline.get_ppl` is the simpler public helper. |
| `repetition_ngram_size` / `repetition_ngram_threshold` | `0` | Non-positive values are clamped to `0`. |

Validation failures are usually assertion errors raised at config creation time. Check ranges before passing user-provided values.

## `Pipeline` Methods

### `infer(...)` and `__call__(...)`

```python
response = pipe.infer("Hello")
responses = pipe(["Hello", "Write a title"], gen_config=gen_config)
```

Accepted prompt shapes for text inference:

- `str` for one prompt.
- `list[str]` for a batch.
- `list[dict]` for one OpenAI-style message list.
- `list[list[dict]]` for batched OpenAI-style conversations.

`infer(...)` also accepts `gen_config`, `do_preprocess`, `adapter_name`, `use_tqdm`, and engine keyword arguments such as `enable_thinking` when supported by the model/backend.

### `stream_infer(...)`

```python
for chunk in pipe.stream_infer(prompts, gen_config=gen_config):
    print(chunk.index, chunk.text, end="")
```

`stream_infer(...)` returns an iterator of `Response` chunks. In batched streaming, use `chunk.index` to group chunks by original prompt order. For session-aware streaming, pass `sessions=pipe.session()` or a list of sessions and manage `sequence_start`, `sequence_end`, and `step` only when you need lower-level control than `chat(...)`.

### `chat(...)` and `session(...)`

```python
session = pipe.chat("Remember that my code word is blue.")
session = pipe.chat("What is my code word?", session=session)
print(session.response.text)
```

`chat(...)` updates a session with prompt, response, token step, and history. With `stream_response=True`, it returns an iterator and updates the session after the iterator is consumed.

Use `pipe.session()` when you need a session before the first turn or when using `stream_infer(...)` directly.

### `get_ppl(...)`

```python
scores = pipe.get_ppl([[1, 2, 3], [4, 5, 6]])
```

`get_ppl(input_ids)` accepts `list[int]` or `list[list[int]]`, requires each sequence to have more than one token, and returns a list of floats. Documentation notes that the returned value is cross-entropy loss without applying exponential afterwards. Long `input_ids` may OOM.

### `get_reward_score(...)` and `get_logits(...)`

`get_reward_score(input_ids)` is limited to supported reward-model architectures. `get_logits(input_ids)` returns scores derived from the final logits. Prefer `GenerationConfig(output_logits=...)` for generation-time logits when the task is tied to generated tokens.

### Resource Management

```python
pipe = pipeline(model_path)
try:
    print(pipe("Hello").text)
finally:
    pipe.close()
```

or:

```python
with pipeline(model_path) as pipe:
    print(pipe("Hello").text)
```

`Pipeline` owns an internal event-loop thread and engine resources; close it in scripts, notebooks, and tests.

## `Response` Fields

`Pipeline` methods return `Response` objects or lists/streams of them. Important fields:

| Field | Meaning |
| --- | --- |
| `text` | Decoded output chunk or final text. |
| `generate_token_len` | Generated token count. |
| `input_token_len` | Prompt token count including chat-template text. |
| `finish_reason` | Usually `"stop"`, `"length"`, or `None` while streaming. |
| `token_ids` | Output token ids. |
| `logprobs` | Top logprobs when requested. |
| `logits` | Logits tensor when requested. |
| `last_hidden_state` | Hidden-state tensor when requested. |
| `index` | Original request index in batched output/streaming. |
| `cached_tokens` | Prefix/cache reuse count when available. |

Streaming chunks can be accumulated with `resp = resp.extend(chunk) if resp else chunk`, matching LMDeploy’s own tests.

## Chat CLI

Use `lmdeploy chat` for local interactive text inference:

```bash
lmdeploy chat org/model-or-local-path --backend turbomind --cache-max-entry-count 0.4
lmdeploy chat org/model-or-local-path --backend pytorch --tp 2 --session-len 4096
```

Useful options include `--backend`, `--chat-template`, `--revision`, `--download-dir`, `--trust-remote-code`, `--dtype`, `--tp`, `--session-len`, `--cache-max-entry-count`, `--enable-prefix-caching`, `--quant-policy`, `--model-format`, PyTorch `--adapters`, PyTorch `--device`, and speculative decoding options. Run `lmdeploy chat --help` for the exact installed CLI surface.

Interactive behavior:

- Double-enter ends one prompt input.
- Type `end` to end the current session.
- Type `exit` to quit.
- `lmdeploy chat` disables metrics and refuses prefix caching for interactive chat.
