# Automation Patterns

Use these patterns to automate MTEB safely from shell scripts, CI jobs, notebooks, or orchestration systems.

## Preflight Without Running Benchmarks

Use help commands and lightweight inventory commands before any evaluation:

```bash
set -euo pipefail

mteb --help >mteb-help.txt
mteb run --help >mteb-run-help.txt
mteb available-tasks --task-types Retrieval --languages eng >mteb-retrieval-eng.txt
```

Validation signals:

- Help commands exit `0`.
- `mteb --help` includes the command you plan to call.
- `mteb run --help` includes required flags such as `--model`, `--tasks`, `--output-folder`, and `--overwrite-strategy`.
- Inventory commands print task or benchmark rows; an empty or unexpectedly small list means filters should be reviewed with `tasks-and-benchmarks`.

Bundled helper equivalent:

```bash
python sub-skills/cli-and-automation/scripts/check_mteb_cli.py
```

## Single Evaluation Script

A conservative run script should make paths explicit and avoid deprecated flags:

```bash
set -euo pipefail

MODEL="sentence-transformers/all-MiniLM-L6-v2"
OUT="results"

mteb run \
  --model "$MODEL" \
  --tasks Banking77Classification \
  --output-folder "$OUT" \
  --overwrite-strategy only-missing \
  --batch-size 32 \
  --no-co2-tracker
```

Automation notes:

- `only-missing` resumes incomplete caches without forcing a full rerun.
- Use `always` only when intentionally invalidating prior results.
- Add `--model-revision` when reproducibility requires a fixed model revision.
- Add `--prediction-folder` only when predictions are needed; predictions can be large and should not be mixed into result metadata paths accidentally.

## Matrix Runs

For a small shell matrix, keep model/task pairs explicit and quote all expansions:

```bash
set -euo pipefail

models=(
  "sentence-transformers/all-MiniLM-L6-v2"
)

tasks=(
  "Banking77Classification"
  "EmotionClassification"
)

for model in "${models[@]}"; do
  for task in "${tasks[@]}"; do
    mteb run \
      --model "$model" \
      --tasks "$task" \
      --output-folder results \
      --overwrite-strategy only-missing \
      --no-co2-tracker
  done
done
```

Prefer explicit tasks for repeatable automation. Use `--languages`, `--task-types`, or `--categories` only after logging the resulting inventory with `mteb available-tasks`.

## Benchmark Runs

Benchmark selection should not be combined with task filters:

```bash
mteb run \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --benchmarks "MTEB(eng, v1)" \
  --output-folder results \
  --overwrite-strategy only-missing
```

If a user passes both `--benchmarks` and task filters, explain that the CLI intentionally warns and ignores task filters. Split the workflow into either benchmark-driven evaluation or task-filter-driven evaluation.

## Metadata Automation

Generate a model card after results are present:

```bash
set -euo pipefail

MODEL="sentence-transformers/all-MiniLM-L6-v2"
REVISION="main"
RESULTS_DIR="results/sentence-transformers__all-MiniLM-L6-v2/${REVISION}"

mteb create-model-results \
  --model-name "$MODEL" \
  --results-folder "$RESULTS_DIR" \
  --output-path model_card.md \
  --overwrite
```

Validation signals:

- `model_card.md` exists after the command.
- The output begins with YAML frontmatter containing MTEB result metadata.
- If the file already exists and `--overwrite` is omitted, failure is expected and protects existing content.

If the installed package exposes `create-meta` instead of `create-model-results`, update only the command name after confirming with `mteb --help`; keep the same path validation logic.

## Leaderboard Automation

For local-only review:

```bash
mteb leaderboard --cache-path results --host 127.0.0.1 --port 7860
```

For a fresh rebuild:

```bash
mteb leaderboard --cache-path results --host 127.0.0.1 --port 7860 --rebuild
```

Automation notes:

- The leaderboard command is a long-running server process; do not run it in a CI step that expects immediate completion.
- Use `--share` only when a public Gradio URL is appropriate.
- Optional leaderboard dependencies may need the package extra that includes the leaderboard stack.

## CLI To Python Escalation

Switch from CLI to Python when automation needs parameters not exposed by the console script:

- Task filters such as `exclude_private`, `exclude_beta`, `exclude_superseded`, `script`, `domains`, `modalities`, `exclude_aggregate`, or exclusive language/modality filtering.
- Evaluation controls such as `raise_error`, `public_only`, `num_proc`, custom timers, or a prebuilt `ResultCache` object.
- Custom model construction with `embed_dim` or additional keyword arguments passed through `mteb.get_model(...)`.

Use the CLI for stable repeatable shell workflows; use Python APIs for fine-grained task selection and programmatic error handling.
