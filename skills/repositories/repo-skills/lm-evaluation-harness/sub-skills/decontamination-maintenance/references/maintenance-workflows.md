# Maintenance Workflows

## Request-cache behavior

LM Evaluation Harness request caching stores preprocessed task request objects. CLI and config paths map the user-facing `--cache_requests` value to evaluator flags:

- `true`: enable request cache reads and writes.
- `refresh`: enable cache and rewrite request-cache entries.
- `delete`: delete request-cache entries instead of evaluating with them.

The default request-cache directory is the package cache directory under `lm_eval/caching/.cache`. If `LM_HARNESS_CACHE_PATH` is set, that environment variable overrides the default path. Cache filenames sanitize path separators and hash overly long cache keys so filenames stay below common filesystem limits.

Use `../scripts/cache_path_advisor.py` to explain the effective path and safe maintenance choices:

```bash
python ../scripts/cache_path_advisor.py
python ../scripts/cache_path_advisor.py --cache-requests refresh --path .cache/lm-eval
```

The advisor does not delete, create, or rewrite cache files.

## Cache maintenance checklist

- Use a dedicated `LM_HARNESS_CACHE_PATH` when comparing branches, containers, or task revisions.
- Use `--cache_requests refresh` after task YAML, prompt construction, few-shot settings, chat templates, rank/world-size settings, or tokenizer/model identity changes.
- Use `--cache_requests delete` when a stale cache is suspected and the user intentionally wants removal.
- Avoid moving raw dataset caches across incompatible hosts or containers; request caches and raw dataset caches are separate concerns.
- After cache code changes, run focused cache unit tests before broad model evaluations.

## Focused maintainer tests

For cache/decontamination edits, prefer the smallest safe tests first:

```bash
python -m pytest tests/test_cache.py
python -m pytest tests/test_cli_subcommands.py -k cache_requests
python -m pytest tests/test_tasks.py -k decontaminate
```

Additional notes:

- `tests/test_janitor.py` is module-skipped in the inspected repo and should not be relied on as an active regression signal without first confirming compatibility.
- `tests/test_requests_caching.py` imports optional model dependencies and may download/load models; classify it as optional/heavy unless the user has the backend stack and network/model cache ready.
- Full suite guidance from contribution docs uses pytest with parallelism and skips the OpenVINO model test; reserve that for final contributor validation.

## Reference-only maintainer scripts

The following repository scripts are useful evidence for maintainers but are not bundled or recommended as default actions:

- `scripts/requests_caching.py`: exercises request caching with a small HF model, but requires torch/transformers and may use GPU/network/model cache.
- `scripts/regression.py`: compares model/task results across branches; it can run many model evaluations and switches git branches.
- `scripts/build_benchmark.py`: generates promptsource task configs and requires promptsource data/templates.
- `scripts/make_gpt2_test_cases.py`: regenerates GPT-2 logprob cases and requires torch/transformers plus model weights.
- Clean-training-data scripts: generate/sort/package training-data ngrams and are multi-day/heavy workflows.

When advising contributors, describe these scripts as maintainer references, not as routine verification commands.

## Regression routing

After editing cache or decontamination code:

1. Run static checks and focused unit tests.
2. If task YAMLs changed, validate task configs and route task authoring details to `../task-authoring/`.
3. If evaluation behavior changed, run a tiny limited evaluation through `../evaluation-runs/`.
4. If result serialization changed, route logging/reporting checks to `../result-logging/`.
5. Only then consider heavier branch regression or request-caching scripts.
