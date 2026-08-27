# Offline Python API Reference

This reference summarizes the vLLM offline APIs that future agents need for Python-only workflows. It is self-contained and does not require reopening the source repository.

## Core Imports

```python
from vllm import LLM, SamplingParams
```

`LLM` initializes the offline engine around a Hugging Face model identifier or local model path. `SamplingParams` controls generation behavior. For pooling models, construct `LLM` with `runner="pooling"` or another model-appropriate runner setting.

## `LLM` Construction

Typical generative setup:

```python
llm = LLM(
    model="facebook/opt-125m",
    tensor_parallel_size=1,
    dtype="auto",
    trust_remote_code=False,
    seed=0,
)
```

Important constructor choices:

- `model`: Hugging Face model id or local model directory supplied by the user.
- `runner`: keep `"auto"` for text generation; use `"pooling"` for embedding, classification, and scoring models when the model requires pooling mode.
- `tokenizer`, `tokenizer_mode`, `revision`, `tokenizer_revision`: pin tokenizer/model sources when reproducibility matters.
- `chat_template`: supply a tokenizer chat template path/string when the model does not include one or the default is unsuitable.
- `trust_remote_code`: keep `False` unless the user explicitly accepts the risk of executing model repository code.
- `dtype`: `"auto"` is the normal default; use explicit `"float16"`, `"bfloat16"`, or `"float32"` only when hardware/model compatibility requires it.
- `tensor_parallel_size`, `gpu_memory_utilization`, `kv_cache_memory_bytes`, `cpu_offload_gb`, `enforce_eager`: hardware/performance levers; avoid changing them for simple correctness fixes unless troubleshooting points there.

Installed API facts for this skill generation showed the public constructor includes `model`, `runner`, `convert`, tokenizer controls, `trust_remote_code`, media guards, `tensor_parallel_size`, `dtype`, quantization options, revisions, `chat_template`, `seed`, GPU memory controls, CPU offload, eager mode, multimodal/pooling/structured output configs, KV cache controls, compilation config, logits processors, speculative decoding aliases, and `**kwargs` forwarded to engine args.

## SamplingParams

Basic deterministic parameters:

```python
sampling_params = SamplingParams(temperature=0.0, max_tokens=16)
```

Common fields:

- `n`: number of completions per prompt; default is `1`.
- `temperature`: randomness; use `0.0` for greedy/deterministic smoke checks, default is `1.0`.
- `top_p`: nucleus sampling probability; default is `1.0`.
- `top_k`: top-k filtering; installed default is `0`.
- `max_tokens`: maximum generated tokens; installed default is `16`, so set it explicitly for short tests and longer answers.
- `presence_penalty`, `frequency_penalty`, `repetition_penalty`: repetition/novelty controls.
- `stop`, `stop_token_ids`, `ignore_eos`: stopping behavior.
- `logprobs`, `prompt_logprobs`: request token log-probability data in the returned objects.
- `structured_outputs`: routes to structured output support; for deep JSON/tool/reasoning guidance, use the structured-tool-reasoning sub-skill.
- `allowed_token_ids`, `bad_words`, `thinking_token_budget`, `repetition_detection`: advanced generation constraints available in current vLLM.

Some models ship a `generation_config.json`. vLLM may apply creator-recommended generation settings by default. If a task needs vLLM defaults rather than model defaults, construct the engine with `generation_config="vllm"` when that engine argument is supported by the installed version.

## Raw Prompt Generation

Use `generate` for completion-style prompts that are already formatted exactly as the model should see them.

```python
prompts = ["Hello, my name is", "The capital of France is"]
sampling_params = SamplingParams(temperature=0.0, max_tokens=8)
outputs = llm.generate(prompts, sampling_params, use_tqdm=False)

for output in outputs:
    text = output.outputs[0].text
    print(output.prompt, text)
```

Output shape:

- `outputs` is a list of `RequestOutput` objects.
- `RequestOutput.prompt` is the raw prompt string when available.
- `RequestOutput.prompt_token_ids` contains prompt token ids when returned.
- `RequestOutput.outputs` is a list of `CompletionOutput` objects, one per requested completion.
- `CompletionOutput.text` is generated text.
- `CompletionOutput.token_ids`, `cumulative_logprob`, `logprobs`, `finish_reason`, and `stop_reason` provide decoding details.

`generate` does not apply a chat template automatically. Do not pass raw OpenAI-style chat messages directly to `generate` unless you first convert them into a model-formatted prompt with the tokenizer chat template.

## Chat Generation

Use `chat` for OpenAI-style message dictionaries in offline Python code.

```python
messages = [
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Say hello in five words."},
]
sampling_params = SamplingParams(temperature=0.0, max_tokens=16)
outputs = llm.chat(messages, sampling_params=sampling_params, use_tqdm=False)
print(outputs[0].outputs[0].text)
```

Batch chat uses a list of conversations:

```python
batch = [
    [{"role": "user", "content": "Write one haiku."}],
    [{"role": "user", "content": "Name one primary color."}],
]
outputs = llm.chat(batch, sampling_params=sampling_params, use_tqdm=False)
```

Chat template rules:

- `LLM.chat` applies the model/tokenizer chat template. If the model lacks a template, pass `chat_template=` to `LLM(...)` or to the chat call when supported.
- `LLM.generate` receives literal prompts and does not auto-template chat messages.
- If manually templating, use the model tokenizer's chat template with `add_generation_prompt=True`, then pass the resulting strings to `generate`.

## Pooling APIs

Pooling models do not return generated text. Use a pooling-capable model and mode:

```python
llm = LLM(model="intfloat/e5-small", runner="pooling", enforce_eager=True)
```

Embedding:

```python
outputs = llm.embed(["A short document"])
embedding = outputs[0].outputs.embedding
hidden_size = outputs[0].outputs.hidden_size
```

Generic encoding for pooling models:

```python
outputs = llm.encode(["A short document"])
pooled_data = outputs[0].outputs.data
```

Classification:

```python
outputs = llm.classify(["A sentence to classify"])
probs = outputs[0].outputs.probs
predicted_class = max(range(len(probs)), key=probs.__getitem__)
```

Scoring/reranking:

```python
query = "What is the capital of France?"
documents = ["Paris is the capital of France.", "Brasilia is in Brazil."]
outputs = llm.score(query, documents)
scores = [output.outputs.score for output in outputs]
```

Pooling output extraction:

- `embed` returns `EmbeddingRequestOutput`; read `output.outputs.embedding`.
- `classify` returns `ClassificationRequestOutput`; read `output.outputs.probs` and optionally `num_classes`.
- `score` returns `ScoringRequestOutput`; read `output.outputs.score`.
- `encode` returns generic pooling outputs; read `output.outputs.data` unless a typed helper converts it.
- Pooling outputs are data objects, not generated text; do not look for `.outputs[0].text` on them.

## Queue-Style Offline APIs

For offline batching without blocking at each call, vLLM exposes queue-oriented methods on `LLM`:

- `enqueue`: enqueue prompts for generation.
- `enqueue_chat`: enqueue chat conversations.
- `wait_for_completion`: wait for all enqueued requests and return results.

Use the synchronous `generate` and `chat` APIs for most scripts. Reach for queue APIs when building a local batch processor that needs to submit multiple request groups before waiting.

## Lower-Level Engine Note

`LLMEngine` and `EngineArgs.from_cli_args(args)` are lower-level APIs for direct engine stepping and CLI-compatible argument parsing. Prefer `LLM` unless the user specifically needs manual request IDs, custom scheduling loops, or engine-step integration.
