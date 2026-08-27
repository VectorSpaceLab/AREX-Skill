# Offline Pipeline Workflows

These workflows are self-contained usage patterns for text LLM inference through LMDeploy. Replace model ids with local paths when downloads are not allowed.

## 1. Safe Config Inspection Without a Model

Before writing inference code in an unfamiliar environment, inspect the installed LMDeploy API without loading weights:

```bash
python sub-skills/pipeline-inference/scripts/inspect_pipeline_config.py --include-cli
```

Use the output to confirm:

- `lmdeploy.pipeline` signature and version.
- `GenerationConfig`, `PytorchEngineConfig`, and `TurbomindEngineConfig` defaults.
- Chat-template registry names available in the installed package.
- Whether `lmdeploy` and `lmdeploy chat` command help can run.

This script imports LMDeploy and may import CLI modules, but it does not instantiate a pipeline, download weights, or contact model hubs.

## 2. Minimal Batch Inference

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline

backend_config = TurbomindEngineConfig(
    tp=1,
    session_len=4096,
    cache_max_entry_count=0.6,
)
gen_config = GenerationConfig(
    max_new_tokens=128,
    do_sample=True,
    top_p=0.9,
    top_k=40,
    temperature=0.7,
)

prompts = [
    "Summarize what LMDeploy is.",
    "Give two tips for reducing inference memory.",
]

with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
    responses = pipe(prompts, gen_config=gen_config)

for response in responses:
    print(response.finish_reason, response.generate_token_len)
    print(response.text)
```

Expected output shape: a list of `Response` objects with `text`, token counts, `finish_reason`, and optional payloads requested through `GenerationConfig`.

## 3. OpenAI-Style Message Prompts

LMDeploy accepts OpenAI-style message lists for offline pipeline calls:

```python
from lmdeploy import GenerationConfig, pipeline

prompts = [
    [{"role": "user", "content": "Write a haiku about GPUs."}],
    [
        {"role": "system", "content": "Answer tersely."},
        {"role": "user", "content": "Define KV cache."},
    ],
]

gen_config = GenerationConfig(max_new_tokens=80)

with pipeline("org/model-or-local-path") as pipe:
    responses = pipe.infer(prompts, gen_config=gen_config)

print([response.text for response in responses])
```

Notes:

- A single `list[dict]` is treated as one conversation.
- A `list[list[dict]]` is treated as a batch.
- For text-only tasks, `content` may be a string. Multimodal content belongs to the `vision-language` sub-skill.
- If a model emits odd role markers or ignores the system message, inspect and override the chat template.

## 4. Streaming Batch Output

```python
from collections import defaultdict
from lmdeploy import GenerationConfig, pipeline

prompts = [
    [{"role": "user", "content": "Count to five."}],
    [{"role": "user", "content": "Name three colors."}],
]
chunks_by_index = defaultdict(list)

with pipeline("org/model-or-local-path") as pipe:
    for chunk in pipe.stream_infer(prompts, gen_config=GenerationConfig(max_new_tokens=64)):
        chunks_by_index[chunk.index].append(chunk.text)
        print(f"[{chunk.index}] {chunk.text}", end="", flush=True)

full_texts = {index: "".join(parts) for index, parts in chunks_by_index.items()}
print(full_texts)
```

Rules of thumb:

- Use `chunk.index` to group batched streams.
- `chunk.finish_reason` may only be meaningful on later/final chunks.
- For one final `Response`, accumulate chunks with `Response.extend` or concatenate text and inspect the last chunk’s metadata.

## 5. Multi-Turn Chat Sessions

Use `Pipeline.chat` for normal multi-turn text conversations:

```python
from lmdeploy import GenerationConfig, pipeline

gen_config = GenerationConfig(max_new_tokens=80)

with pipeline("org/model-or-local-path") as pipe:
    session = pipe.chat("Remember this passphrase: blue raven.", gen_config=gen_config)
    session = pipe.chat("What passphrase did I give you?", session=session, gen_config=gen_config)
    print(session.response.text)
    print(session.history)
```

Use streaming chat when the UI should print tokens as they arrive:

```python
with pipeline("org/model-or-local-path") as pipe:
    session = pipe.session()
    for chunk in pipe.chat(
        "Tell a short story.",
        session=session,
        stream_response=True,
        gen_config=GenerationConfig(max_new_tokens=120),
    ):
        print(chunk.text, end="", flush=True)
    print("\nturns:", len(session.history))
```

If you call `stream_infer` directly with sessions, keep the number of sessions equal to the number of prompts. Let `chat` manage `step`, `history`, and `sequence_start` unless you are reproducing a lower-level test or custom session protocol.

## 6. Per-Prompt Generation Configs

`Pipeline.infer` accepts one `GenerationConfig` for all prompts or a list matching the prompt count:

```python
from lmdeploy import GenerationConfig, pipeline

prompts = ["Give a short title.", "Explain tokenization in detail."]
gen_configs = [
    GenerationConfig(max_new_tokens=12),
    GenerationConfig(max_new_tokens=160, do_sample=True, temperature=0.8),
]

with pipeline("org/model-or-local-path") as pipe:
    responses = pipe.infer(prompts, gen_config=gen_configs)
```

A length mismatch raises `ValueError`. Validate list lengths before passing user-supplied batches.

## 7. Logits and Last Hidden States

Request generated-token logits or hidden states through `GenerationConfig`:

```python
from lmdeploy import GenerationConfig, pipeline

gen_config = GenerationConfig(
    max_new_tokens=10,
    output_logits="generation",
    output_last_hidden_state="generation",
)

with pipeline("org/model-or-local-path") as pipe:
    responses = pipe(["Say hello."], gen_config=gen_config)

logits = responses[0].logits
hidden_state = responses[0].last_hidden_state
print(logits.shape if logits is not None else None)
print(hidden_state.shape if hidden_state is not None else None)
```

Cautions:

- `"all"` can be much larger than `"generation"`.
- Tensor payloads increase memory use and serialization cost.
- Backend/model combinations may differ in support; design callers to tolerate `None` and report unsupported payloads clearly.

## 8. Prompt PPL / Cross-Entropy

Use a tokenizer to turn text or chat messages into input ids, then call `Pipeline.get_ppl`:

```python
from transformers import AutoTokenizer
from lmdeploy import pipeline

model_path = "org/model-or-local-path"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
input_ids = tokenizer.encode("This is a test sentence.")

with pipeline(model_path) as pipe:
    scores = pipe.get_ppl(input_ids)

print(scores)
```

For chat models, prefer the tokenizer’s chat-template helper when available:

```python
messages = [{"role": "user", "content": "Hello, how are you?"}]
input_ids = tokenizer.apply_chat_template(messages)
```

`get_ppl` returns cross-entropy loss values without exponentiation. Each input sequence must contain more than one token. Long inputs can OOM.

## 9. PyTorch Backend With LoRA Adapter

```python
from lmdeploy import GenerationConfig, PytorchEngineConfig, pipeline

backend_config = PytorchEngineConfig(
    session_len=2048,
    cache_max_entry_count=0.5,
    adapters={"lora_name_1": "org/lora-adapter-or-local-path"},
)

gen_config = GenerationConfig(max_new_tokens=128, top_p=0.8, top_k=40, temperature=0.8)

with pipeline("org/base-model-or-local-path", backend_config=backend_config) as pipe:
    response = pipe(
        [[{"role": "user", "content": "Write one sentence in the adapter style."}]],
        gen_config=gen_config,
        adapter_name="lora_name_1",
    )
    print(response[0].text)
```

CLI equivalent for interactive chat uses `--adapters`; multiple adapters must be `name=path` pairs:

```bash
lmdeploy chat org/base-model-or-local-path --backend pytorch --adapters lora_name_1=org/lora-adapter-or-local-path
```

If a LoRA adapter requires a special chat template, register or load the template, then pass matching `chat_template_config` and `adapter_name`.

## 10. CLI Interactive Chat

```bash
lmdeploy chat org/model-or-local-path --backend turbomind --cache-max-entry-count 0.4 --session-len 4096
lmdeploy chat org/model-or-local-path --backend pytorch --tp 2 --cache-max-entry-count 0.4
```

Operational notes:

- Double-enter submits a prompt.
- Type `end` to end the current session.
- Type `exit` to quit.
- Use `--chat-template <name-or-json-file>` to override formatting.
- Use `--trust-remote-code` only after reviewing the model repository and accepting that arbitrary remote model code may execute.

## 11. Tensor Parallelism and Multiprocessing Guard

For TurboMind tensor parallelism:

```python
from lmdeploy import TurbomindEngineConfig, pipeline

with pipeline("org/model-or-local-path", backend_config=TurbomindEngineConfig(tp=2)) as pipe:
    print(pipe("Hello").text)
```

For PyTorch `tp > 1`, protect script entry to avoid Python multiprocessing bootstrap errors:

```python
from lmdeploy import PytorchEngineConfig, pipeline


def main():
    backend_config = PytorchEngineConfig(tp=2, session_len=4096)
    with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
        print(pipe("Hello").text)


if __name__ == "__main__":
    main()
```

## 12. OOM-First Rewrite Pattern

If a user gives an OOMing script, first reduce KV-cache allocation and generation length before changing the model:

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline

backend_config = TurbomindEngineConfig(
    cache_max_entry_count=0.2,
    session_len=2048,
    max_batch_size=1,
)
gen_config = GenerationConfig(max_new_tokens=64)

with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
    print(pipe("Short diagnostic prompt", gen_config=gen_config).text)
```

If that works, raise `cache_max_entry_count`, `session_len`, `max_batch_size`, and `max_new_tokens` gradually while monitoring memory. For CLI, pass `--cache-max-entry-count 0.2`.

## 13. No-Model Draft for Batch Prompts With Logits/PPL

When a task asks for code structure but no model execution, keep execution behind a function and validate only config construction:

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline


def build_configs():
    backend_config = TurbomindEngineConfig(cache_max_entry_count=0.5, session_len=4096)
    gen_config = GenerationConfig(max_new_tokens=16, output_logits="generation")
    return backend_config, gen_config


def run(model_path):
    backend_config, gen_config = build_configs()
    prompts = [[{"role": "user", "content": "Return one JSON key named answer."}]]
    with pipeline(model_path, backend_config=backend_config) as pipe:
        responses = pipe.infer(prompts, gen_config=gen_config)
        ppl = pipe.get_ppl([responses[0].token_ids]) if len(responses[0].token_ids) > 1 else None
        return responses, ppl
```

Do not call `run(...)` in tests or scripts that must avoid downloads/GPU usage. Use the inspection script for safe validation.
