# Provider and cache notes

## OpenAI SDK compatibility

YiVal baseline code uses the legacy OpenAI SDK style:

```python
openai.ChatCompletion.create(model=..., messages=...)
```

The package metadata pins `openai = 0.27.10`. If the active environment uses a newer OpenAI SDK that removed `ChatCompletion`, provider-backed generators/evaluators may fail even if imports pass.

## Credentials

Provider-backed paths commonly need:

- `OPENAI_API_KEY` for OpenAI chat completions, prompt generation, OpenAI prompt evaluator, OpenAI Elo, and packaged demos.
- Replicate tokens for demos or fine-tuning utilities that use Replicate models.
- Google credentials for document generator `source: drive`.
- Network access for Hugging Face dataset-server URLs and AlpacaEval annotators.

Do not run provider-backed commands without explicit approval for credentials, network, and cost.

## Caching

Set `output_path` for every provider-backed generator:

```yaml
output_path: generated_examples.pkl
```

Behavior:

- If the pickle path exists, the generator loads it and yields cached content.
- If absent, the generator calls the provider until it collects the requested count, then writes the pickle.
- Optional `output_csv_path` can export generated input examples as CSV.

Keep caches task-specific. Do not reuse prompt-generation caches across different input schemas.

## Reducing cost and failure risk

- Start with `number_of_examples: 1` or `2`.
- Start with `number_of_variations: 1` or `2`.
- Use manual variations as baselines.
- Avoid `diversify: true` until the plain generation path works.
- Keep `max_tokens` bounded.
- Use deterministic offline generators (`chain_of_density_prompt_generator`, `self_exemplar`) when provider calls are not necessary.
