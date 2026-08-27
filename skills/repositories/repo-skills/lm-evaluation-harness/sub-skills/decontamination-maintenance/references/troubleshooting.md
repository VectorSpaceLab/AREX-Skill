# Troubleshooting

## Decontamination config warnings

`should_decontaminate: true` but no query:
- Add a `doc_to_decontamination_query` that identifies the evaluated example, or document why the task implementation intentionally falls back to `doc_to_text`.
- For YAML tasks, prefer a field name or Jinja expression that includes prompt source text, not the model target alone.

Query present while decontamination is disabled:
- Treat this as inactive configuration. It may be intentional staging, but clean metrics will not be produced from it until decontamination is enabled and artifacts are supplied.

YAML parsing fails on `!function`:
- Some task YAMLs use custom tags loaded by the harness. Static tools can flag this as requiring harness validation; do not execute the referenced Python just to inspect hygiene.

## Missing ngram artifacts

Common setup failures:

- `info.json` is absent from the ngram directory.
- `info.json` lacks `ngram_size` or records an unexpected value.
- No sorted bucket files such as `*.sorted.zst` are present.
- Artifacts were generated with a different ngram size than the task/evaluation expects.

Safe response:

- Do not start generating Pile ngrams automatically.
- Ask whether the user already has prepared artifacts.
- Provide the artifact checklist and explain that generation/sorting/packaging can take days and significant disk/network resources.

## Reproducibility footgun

Set `PYTHONHASHSEED=0` before ngram generation. Bucket assignment depends on hashing, and a fixed hash seed makes interrupted/restarted generation more reproducible.

If buckets were generated without a fixed hash seed, recommend regenerating or treating cross-run bucket layout comparisons as unreliable.

## Cache path staleness

Symptoms:

- Evaluation appears to ignore recent task/prompt edits.
- Different branches or containers reuse unexpected request-cache files.
- Long model names or endpoint identifiers create hard-to-read cache filenames.

Actions:

- Inspect `LM_HARNESS_CACHE_PATH`; if set, it overrides the default package cache path.
- Use a branch- or experiment-specific cache directory for comparisons.
- Use `--cache_requests refresh` after changes that alter request construction.
- Use `--cache_requests delete` only when the user intentionally wants cache removal.
- Remember that request caches are not the same as raw dataset caches.

## Unsafe-code and dataset/network dependence

Some tasks or configurations may require trusted remote code, dataset downloads, API credentials, or optional model backends. Do not treat static decontamination review as proof that a full evaluation is safe to run.

Before running maintainer scripts or model-backed tests, check for:

- Optional extras such as torch, transformers, promptsource, or backend-specific packages.
- Network/model-cache availability.
- Dataset trust settings and unsafe-code requirements.
- GPU/backend assumptions.

## Focused test selection

Use these tests as initial signals after cache/decontamination changes:

```bash
python -m pytest tests/test_cache.py
python -m pytest tests/test_cli_subcommands.py -k cache_requests
python -m pytest tests/test_tasks.py -k decontaminate
```

Escalate only when needed:

- `tests/test_requests_caching.py` is optional/heavy because it can load model dependencies.
- `tests/test_janitor.py` is skipped in the inspected repo and is not an active pass/fail signal.
- Branch regression scripts can switch git branches and run many model evaluations; do not use them as first-line checks.
