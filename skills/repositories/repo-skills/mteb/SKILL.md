---
name: mteb
description: "Use MTEB to evaluate embedding models, select tasks and
  benchmarks, validate model protocols, run CLI workflows, inspect result
  caches, and contribute tasks/models/benchmarks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MTEB

Use this skill when working with MTEB, the Massive Text Embedding Benchmark package for evaluating text, multimodal, and retrieval embedding systems. It routes common agent tasks across evaluation, task selection, model wrappers, command-line automation, result analysis, leaderboard workflows, and repository contributions.

## Start Here

- Install with `pip install mteb`; add extras only for the workflow that needs them, such as `mteb[leaderboard]`, `mteb[codecarbon]`, `mteb[image]`, `mteb[audio]`, or model-provider extras.
- Verify the environment with `python -c "import mteb; print(mteb.__version__)"` and `mteb --help` before writing automation.
- Use explicit cache folders such as `mteb.ResultCache(cache_path="mteb-results-cache")` or `mteb run --output-folder mteb-results-cache` for reproducible runs.
- Prefer small named tasks and CPU-safe models while debugging; full benchmarks can download datasets and run expensive model inference.
- Read `references/repo-provenance.md` when deciding whether this skill matches the current MTEB release.
- Read `references/troubleshooting.md` for cross-cutting install, import, optional dependency, task download, CLI, cache, and result issues.

## Route By User Intent

- **Run an evaluation from Python**: Use `sub-skills/evaluation-workflows/SKILL.md` for `mteb.evaluate(...)`, overwrite strategies, `ResultCache`, predictions, CO2 tracking, failure tolerance, and mock smoke checks.
- **Choose tasks or benchmarks**: Use `sub-skills/tasks-and-benchmarks/SKILL.md` for `mteb.get_tasks(...)`, `mteb.get_task(...)`, `mteb.get_benchmark(...)`, languages, scripts, domains, task types, categories, modalities, beta/private/superseded behavior, and metadata inspection.
- **Load or validate a model**: Use `sub-skills/models-and-encoders/SKILL.md` for `mteb.get_model(...)`, `ModelMeta`, SentenceTransformers/CrossEncoder compatibility, custom encoder/search protocols, prompts, cache/compression wrappers, BM25, and optional model dependencies.
- **Use the CLI or automate shell workflows**: Use `sub-skills/cli-and-automation/SKILL.md` for `mteb run`, `available-tasks`, `available-benchmarks`, `create-model-results`, `leaderboard`, help checks, and CI-safe command validation.
- **Inspect results or leaderboard outputs**: Use `sub-skills/results-and-leaderboard/SKILL.md` for result cache layout, `ResultCache`, `BenchmarkResults`, dataframes, model-card result metadata, result submission, and local leaderboard caveats.
- **Contribute to MTEB**: Use `sub-skills/contributing-to-mteb/SKILL.md` for adding tasks/datasets, benchmarks, model metadata/implementations, citations, descriptive stats, and pre-PR validation.

## Minimal Evaluation Pattern

```python
import mteb

model = mteb.get_model("mteb/baseline-random-encoder")
tasks = mteb.get_tasks(tasks=["Banking77Classification.v2"])
cache = mteb.ResultCache(cache_path="mteb-results-cache")

results = mteb.evaluate(
    model,
    tasks=tasks,
    cache=cache,
    overwrite_strategy="only-missing",
    co2_tracker=False,
)
print(results.model_name, len(results.task_results))
```

## Minimal CLI Pattern

```bash
mteb run \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --tasks Banking77Classification.v2 \
  --output-folder mteb-results-cache \
  --overwrite-strategy only-missing \
  --no-co2-tracker
```

## Shared References And Scripts

- `references/api-surface.md` summarizes the top-level APIs and CLI command surface used by multiple sub-skills.
- `references/troubleshooting.md` covers cross-cutting failures before routing to a sub-skill-specific troubleshooting file.
- `scripts/check_mteb_environment.py` verifies package import, version, CLI availability, and key API signatures without running benchmarks or downloading datasets.

## Decision Points

- **Python vs CLI**: Use Python for fine-grained filtering, custom encoders, and result dataframes; use CLI for reproducible shell runs and simple automation.
- **Task names vs filters**: Named `tasks=[...]` selection takes precedence over broad filters; for combined logic, select/filter explicitly and inspect metadata.
- **Benchmarks vs ad hoc tasks**: Benchmarks encode official task/split/language selections; do not mix benchmark selection with task/language filters unless intentionally ignoring the filters.
- **Cache overwrite mode**: Use `only-missing` for resumable work, `only-cache` for offline inspection, `never` to protect existing results, and `always` for forced recomputation.
- **Optional dependencies**: Install extras only for the selected workflow; many model, audio, image, leaderboard, and provider integrations are optional and can be heavy.
- **Private/beta/superseded tasks**: Defaults hide or warn about risky tasks; opt in only when the user requests them and has dataset access.

## Validation Checklist

- `import mteb` and `mteb --help` both work in the target environment.
- The selected tasks and benchmarks are visible with the same filters the user will run.
- The model object satisfies the protocol required by the chosen task type and modality.
- The cache path is explicit and points to the intended local or remote result root.
- Optional extras are installed only when the workflow needs them.
- Result or leaderboard workflows validate folder layout before publishing or comparing scores.
