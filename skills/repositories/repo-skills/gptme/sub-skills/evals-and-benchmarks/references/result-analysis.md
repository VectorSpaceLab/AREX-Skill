# Result Analysis

This reference covers the files written by eval runs, the leaderboard generators, trend analysis, and how to interpret pass rates and model/tool-format comparisons.

## What the raw files mean

Each eval run writes a timestamped result tree.

Key files:

- `eval_results/<timestamp>/eval_results.csv` — one row per test and model/format pair.
- `eval_results/<timestamp>/eval_results.json` — JSON summary when `--json` is enabled.
- `cases.csv` — per-checker pass/fail rows for each test.
- `gen_stdout.txt` / `gen_stderr.txt` — generation logs.
- `run_stdout.txt` / `run_stderr.txt` — execution and checker logs.

Interpretation rules:

- `Passed=true` means every checker passed for that test.
- `Score` is partial credit in `passed_count/total_count` form.
- `Tool Calls` counts runnable tool uses in the parent conversation log.
- `Num Steps` is the number of LLM request/response turns.
- `Cost USD` may be empty when pricing data is unavailable.
- `Log Dir` and `Workspace Dir` tell you where the run actually lived.

If you only have a tiny CSV with `Test` and `Passed` columns, the bundled summarizer can still report pass/fail counts and test names.

## Leaderboard outputs

The main summary path is `gptme-eval --leaderboard`.

Supported output formats:

- `rst`
- `csv`
- `markdown`
- `json`
- `html`

Examples:

```bash
gptme-eval --leaderboard --leaderboard-format markdown
gptme-eval --leaderboard --leaderboard-format csv
gptme-eval --leaderboard --leaderboard-format html
gptme-eval --leaderboard --leaderboard-format rst
```

What the leaderboard does:

- loads timestamped `eval_results.csv` files from `eval_results/` or `EVAL_RESULTS_DIR`,
- groups rows by model and tool format,
- picks the best tool format per model,
- ranks models with a Wilson lower bound score (z=1.0) so tiny sample sizes do not dominate,
- applies the `--min-tests` threshold before ranking.

Good comparison habits:

- compare one model at a time when you care about format sensitivity,
- keep `--timeout` and `--parallel` fixed,
- record whether Docker was used,
- do not compare a `--no-lessons` baseline with a lesson-injected run unless that difference is deliberate.

## Per-test breakdowns

The installed module CLI also exposes a per-test view:

```bash
python -m gptme.eval.leaderboard --per-test --format markdown
python -m gptme.eval.leaderboard --per-test --format html
```

The per-test view:

- groups tests into `basic`, `practical`, and `other`,
- uses `P`, `F`, and `-` markers for pass/fail/not-tested,
- is useful when you need to see which exact tests changed between two models or formats.

## Trend outputs

There are two trend views and they answer different questions.

### 1) Aggregate leaderboard trends

`gptme-eval --leaderboard --trends` shows daily pass-rate history from timestamped result directories.

Example:

```bash
gptme-eval --leaderboard --trends --leaderboard-format markdown --trend-days 30
gptme-eval --leaderboard --trends --leaderboard-format html --trend-days 90
```

This view is best when you want:

- a model-level trend line,
- a quick look at recent movement,
- a compact report for a run window.

### 2) Per-test regression/improvement trends

The standalone trends module and shim track test-level changes:

```bash
python -m gptme.eval.trends --format table
python -m gptme.eval.trends --diff --format json
```

The trend detector:

- compares the last two runs per model/test,
- flags regressions and improvements,
- classifies flaky tests when a test has at least four runs and a pass rate between 10% and 90%,
- supports `--last` to limit the history window,
- supports `--model` as a substring filter.

Use this when a model’s overall score is stable but individual tests moved.

## Pass-rate gates and lesson injection

The eval runner can consult a pass-rate gate file to decide whether lessons should be injected or suppressed for a given `(model, eval)` pair.

Important facts:

- the gate is opt-in,
- the environment variable is `GPTME_EVAL_PASS_RATE_GATE_FILE`,
- missing or malformed data falls back to the runner’s normal logic,
- exact model keys win before any normalized OpenRouter fallback is considered.

When analyzing a comparison, record whether the run used:

- `--no-lessons`,
- a pass-rate gate file,
- a different provider alias or OpenRouter prefix.

Otherwise two runs can look like a benchmark regression when they actually used different lesson policy.

## Which report to use

- Use `csv` when you want spreadsheet-friendly output.
- Use `markdown` for quick sharing in a chat or issue.
- Use `rst` when you need docs-friendly output.
- Use `json` for downstream scripting.
- Use `html` when you want a self-contained publishable page.

For local triage, start with the bundled summarizer script, then move to leaderboard or trend reports only if you need ranked or time-series analysis.
