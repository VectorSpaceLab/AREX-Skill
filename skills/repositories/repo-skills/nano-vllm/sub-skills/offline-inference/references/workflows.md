# Generation workflows

## Prepare a local model directory

Use a local directory exported by Hugging Face tooling. It should contain a
Qwen3 `config.json`, tokenizer files, and the model's `safetensors` shards. A
remote identifier or a directory containing only a tokenizer is insufficient.
Keep weights outside application source and pass the directory with `--model`.

Before loading weights:

```bash
python ../../scripts/check_env.py --require-cuda
python scripts/run_generation.py --help
```

From the root of this generated skill use `python scripts/check_env.py`; from
this sub-skill directory use `python ../../scripts/check_env.py`. The second
command does not load a model.

## Plain strings

```python
from nanovllm import LLM, SamplingParams

llm = LLM(
    model_dir,
    enforce_eager=True,
    tensor_parallel_size=1,
    max_model_len=2048,
)
params = SamplingParams(temperature=0.6, max_tokens=128)
outputs = llm.generate(
    ["Introduce yourself.", "List three uses of KV caching."],
    params,
    use_tqdm=False,
)
for output in outputs:
    print(output["text"])
llm.exit()
```

Start with one or two prompts and a small token budget. Once this works, raise
batching and length limits through the performance route.

## Chat templates

Nano-vLLM does not apply chat templates itself. Load the tokenizer with
`transformers.AutoTokenizer`, format each conversation with
`apply_chat_template(..., tokenize=False, add_generation_prompt=True)`, and
pass the resulting strings to `generate`. The bundled wrapper applies this
behavior by default when a tokenizer can be loaded; use `--no-chat-template`
for already-formatted prompts.

A minimal conversation shape is:

```python
messages = [{"role": "user", "content": "Explain prefix caching."}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
```

## Token-id prompts and per-request settings

Use token-id prompts when a caller already owns tokenization or when a
benchmark needs controlled lengths:

```python
prompts = [[101, 102, 103], [201, 202]]
settings = [
    SamplingParams(temperature=0.7, max_tokens=32),
    SamplingParams(temperature=1.0, max_tokens=16, ignore_eos=True),
]
outputs = llm.generate(prompts, settings, use_tqdm=False)
```

Every prompt must contain at least one token because the engine reads the last
prompt token during decode. Do not pass a single `SamplingParams` list with a
different length than `prompts`.

## Validation and shutdown

Assert `len(outputs) == len(prompts)`, inspect both output fields, and record
prompt/config metadata outside the engine if reproducibility matters. For
correctness triage use `enforce_eager=True`; for performance comparisons keep
the same model, prompt token lengths, max lengths, and EOS policy across runs.
Explicitly call `exit()` in scripts that create the engine outside a short-lived
process.
