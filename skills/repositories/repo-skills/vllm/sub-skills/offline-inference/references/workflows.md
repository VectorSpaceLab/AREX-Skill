# Offline Inference Workflows

These workflows are designed for future agents writing or debugging Python code that uses vLLM directly. They intentionally avoid server lifecycle topics.

## Workflow: Minimal Text Generation

Use this for completion-style prompts.

```python
from vllm import LLM, SamplingParams

llm = LLM(model="USER_SUPPLIED_MODEL", trust_remote_code=False)
params = SamplingParams(temperature=0.0, max_tokens=16)
outputs = llm.generate(["The capital of France is"], params, use_tqdm=False)
print(outputs[0].outputs[0].text)
```

Validation checks:

- The model identifier or path is supplied by the user and may download weights if it points to a remote hub model.
- The call returns a non-empty list of `RequestOutput` objects.
- Generated text is read from `outputs[0].outputs[0].text`.
- `max_tokens` is explicitly set so a smoke check stays short.

## Workflow: Convert Raw Prompt Code to Offline Chat

When the user has an instruct/chat model and wants chat behavior without a server, change raw prompts into message dictionaries and call `LLM.chat`.

Before conceptually:

```python
outputs = llm.generate([{"role": "user", "content": "Hello"}], params)
```

Correct offline chat pattern:

```python
messages = [{"role": "user", "content": "Hello"}]
outputs = llm.chat(messages, sampling_params=params, use_tqdm=False)
reply = outputs[0].outputs[0].text
```

Important checks:

- `generate` does not auto-apply chat templates.
- `chat` expects one conversation as `list[dict]` or a batch as `list[list[dict]]`.
- If the tokenizer lacks a chat template, pass a suitable `chat_template` when constructing `LLM` or when calling `chat` if supported.
- Preserve `SamplingParams`; do not move sampling controls into message dictionaries.

## Workflow: Manual Chat Template Then Generate

Use this only when the user must call `generate`, for example to feed preformatted prompt strings into a larger completion pipeline.

```python
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

model = "USER_SUPPLIED_CHAT_MODEL"
tokenizer = AutoTokenizer.from_pretrained(model)
conversations = [[{"role": "user", "content": "Hello"}]]
prompts = tokenizer.apply_chat_template(
    conversations,
    tokenize=False,
    add_generation_prompt=True,
)
llm = LLM(model=model)
outputs = llm.generate(prompts, SamplingParams(max_tokens=16), use_tqdm=False)
```

Validation checks:

- The templated `prompts` are strings, not message dictionaries.
- The tokenizer and model are the same revision unless intentionally overridden.
- The user accepts any model download or gated-access requirements.

## Workflow: Batch Multiple Prompts

```python
prompts = ["A", "B", "C"]
params = SamplingParams(temperature=0.0, max_tokens=8)
outputs = llm.generate(prompts, sampling_params=params, use_tqdm=False)
texts = [output.outputs[0].text for output in outputs]
```

If each prompt needs different generation settings, pass a list of `SamplingParams` with the same length as `prompts`. Tests exercise that length mismatches are invalid, while a single `SamplingParams` applies to every prompt.

## Workflow: Pooling Outputs Are Not Text

Embedding:

```python
llm = LLM(model="USER_SUPPLIED_EMBED_MODEL", runner="pooling", enforce_eager=True)
outputs = llm.embed(["hello"])
vector = outputs[0].outputs.embedding
```

Classification:

```python
llm = LLM(model="USER_SUPPLIED_CLASSIFIER", runner="pooling", enforce_eager=True)
outputs = llm.classify(["hello"])
probs = outputs[0].outputs.probs
```

Scoring:

```python
llm = LLM(model="USER_SUPPLIED_RERANKER", runner="pooling", enforce_eager=True)
outputs = llm.score("query", ["document one", "document two"])
scores = [output.outputs.score for output in outputs]
```

Validation checks:

- Use a model that supports the selected pooling task.
- Use `runner="pooling"` when the model/example requires pooling mode.
- Extract `embedding`, `probs`, `score`, or generic `data`, not generated text.

## Workflow: Safe Local Smoke Check

From this installed sub-skill directory, the bundled script is safe by default:

```bash
python scripts/offline_api_smoke.py --print-plan
```

If running from another working directory, resolve `offline_api_smoke.py` from this sub-skill's `scripts/` directory. The script only imports vLLM and prints the planned code path unless a model is supplied and `--skip-run` is not set:

```bash
python scripts/offline_api_smoke.py \
  --model USER_SUPPLIED_MODEL \
  --prompt "The capital of France is" \
  --max-tokens 8
```

Chat smoke check:

```bash
python scripts/offline_api_smoke.py \
  --model USER_SUPPLIED_CHAT_MODEL \
  --chat \
  --prompt "Reply with one word: ready" \
  --max-tokens 4
```

Expected successful signals:

- Import line reports the installed vLLM version when available.
- Plan shows `LLM.generate` or `LLM.chat` based on `--chat`.
- A real run prints `RESULT 0:` followed by generated text.

Hardware/model caveats:

- Supplying a remote model id may download model files.
- GPU execution depends on a compatible backend, driver, PyTorch build, and model dtype.
- CPU/precompiled inspection can prove import and CLI availability, but not GPU runtime correctness.

## Workflow: Determinism-Oriented Debug Run

For reproducible smoke checks:

```python
llm = LLM(model="USER_SUPPLIED_MODEL", seed=0, enforce_eager=True)
params = SamplingParams(temperature=0.0, max_tokens=8)
outputs = llm.generate(["2 + 2 ="], params, use_tqdm=False)
```

Use `temperature=0.0`, short `max_tokens`, and a fixed `seed`. Exact text can still vary across model versions, tokenizer revisions, hardware kernels, and generation config, so tests should assert structural behavior unless the model and environment are fully pinned.
