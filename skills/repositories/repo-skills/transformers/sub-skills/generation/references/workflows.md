# Generation Workflows

## Choose a Decoding Strategy

Start from the behavior the user wants, not from a long list of generation kwargs.

1. Set `max_new_tokens` explicitly.
2. Choose deterministic, sampling, beam, or beam-sampling.
3. Add only the parameters used by that strategy.
4. Set token IDs (`pad_token_id`, `eos_token_id`) when batching, padding, or decoder-only models are involved.
5. Validate with `scripts/generation_config_smoke.py` before wiring the config into model code.

Examples:

```python
# Deterministic, low surprise
GenerationConfig(max_new_tokens=64, do_sample=False, num_beams=1)

# Creative but bounded
GenerationConfig(max_new_tokens=128, do_sample=True, temperature=0.8, top_p=0.9)

# Input-grounded beam search
GenerationConfig(max_new_tokens=80, do_sample=False, num_beams=4, early_stopping=True)
```

Expected signals:

- Deterministic config has no sampling-only controls.
- Sampling config has `do_sample=True` and finite `temperature > 0`.
- Beam config has `num_beams > 1`; `num_return_sequences` does not exceed `num_beams` unless sampling semantics explicitly allow it.

## Save and Reload a Generation Config

Use this when defaults belong with an application, checkpoint, or reproducible experiment.

```python
from transformers import GenerationConfig

config = GenerationConfig(max_new_tokens=128, do_sample=True, top_p=0.9)
config.save_pretrained("./my-generation-config")
loaded = GenerationConfig.from_pretrained("./my-generation-config")
```

Do not commit private tokens, local cache paths, or machine-specific model locations into saved configs.

## Chat Generation With Templates

Use structured chat messages whenever the model is instruction/chat tuned.

```python
messages = [
    {"role": "system", "content": "Answer with one paragraph."},
    {"role": "user", "content": "What does a logits processor do?"},
]
model_inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_tensors="pt",
).to(model.device)
outputs = model.generate(model_inputs, max_new_tokens=96, do_sample=True, temperature=0.7)
```

Validation checks:

- Every message has a supported `role` and `content`.
- `add_generation_prompt=True` is used for a new assistant answer.
- `continue_final_message=True` is used only when the final assistant message is a prefix to continue.
- Template-specific fields such as reasoning controls are passed through documented template kwargs and tested on the target tokenizer.

If a tokenizer has no chat template, route to `../tokenizers-processors/SKILL.md` to define or select the proper template rather than inventing control tokens in generation code.

## Streaming Generation

Use streamers for incremental UI or server push behavior.

```python
from threading import Thread
from transformers import TextIteratorStreamer

streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, timeout=10.0, skip_special_tokens=True)
thread = Thread(
    target=model.generate,
    kwargs=dict(**inputs, streamer=streamer, max_new_tokens=128),
)
thread.start()
for chunk in streamer:
    print(chunk, end="", flush=True)
thread.join(timeout=30.0)
```

Hardening checklist:

- Put generation in a background thread; do not call `generate` synchronously before iterating.
- Set `timeout` to avoid indefinite hangs when model execution errors.
- Join the thread and surface exceptions through application logging.
- Keep tokenizer decoding options (`skip_special_tokens`, cleanup spacing) consistent with non-streaming decode.

## Custom Logits Processors and Stopping Criteria

Use custom logic only after built-in config options are insufficient.

```python
from transformers import LogitsProcessor, LogitsProcessorList, StoppingCriteria, StoppingCriteriaList

class BanTokenProcessor(LogitsProcessor):
    def __init__(self, token_id):
        self.token_id = token_id

    def __call__(self, input_ids, scores):
        scores[:, self.token_id] = -float("inf")
        return scores

processors = LogitsProcessorList([BanTokenProcessor(token_id=tokenizer.eos_token_id)])
outputs = model.generate(**inputs, logits_processor=processors, max_new_tokens=32)
```

Review questions:

- Does the processor run on the same device and dtype as `scores`?
- Can multiple processors mask all valid next tokens?
- Does the stopping criterion terminate for every batch item?
- Is output reproducibility affected by sampling, random seeds, or processor state?

## Custom Generation Methods

Transformers supports custom generation methods for specialized decoding loops and research experiments. Treat these as advanced workflows.

Safe agent approach:

1. Prefer `generate(...)` plus config, processors, and stopping criteria.
2. If a custom loop is required, preserve input preparation, attention masks, cache handling, and stopping criteria.
3. Keep the custom method packaged with its dependencies and tests; do not rely on a loose source checkout.
4. Require `trust_remote_code=True` only when using trusted custom code from a known source.

## No-download Config Review

Before model-backed tests are available, validate the config itself:

```bash
python scripts/generation_config_smoke.py \
  --config-json generation_config.json --strict
```

Expected checks include JSON object shape, valid numeric ranges, sampling contradictions, length conflicts, and token ID consistency. This does not prove model quality or backend availability.
