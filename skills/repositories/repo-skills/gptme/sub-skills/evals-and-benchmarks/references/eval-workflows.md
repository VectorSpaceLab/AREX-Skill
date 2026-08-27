# Eval Workflows

This reference covers the execution paths this sub-skill owns: local gptme eval suites, Docker-isolated runs, SWE-bench, T-bench, and model/tool-format comparison.

## Core eval CLI

The main entry point is `gptme-eval`.

Typical patterns:

```bash
gptme-eval --list
gptme-eval hello --model anthropic/claude-sonnet-4-6
gptme-eval hello --model anthropic/claude-sonnet-4-6 --tool-format tool
gptme-eval sort-and-filter rename-function --model anthropic/claude-sonnet-4-6@xml
gptme-eval all-practical --model anthropic/claude-sonnet-4-6
gptme-eval all --model anthropic/claude-sonnet-4-6
```

Important command rules:

- `--model` can be repeated.
- A model spec may already include a format suffix such as `model@tool`.
- If no format suffix is present and `--tool-format` is supplied, that format is used for the run.
- If no format suffix and no `--tool-format` are supplied, the runner tests all formats (`markdown`, `xml`, `tool`).
- Suite families include `basic`, `browser`, `init_projects`, and the `practical` chain (`practical`, `practical2`, ...).
- `all-practical` expands to every practical suite; `all` expands to every suite.
- Individual test names are also valid once you have them from `gptme-eval --list`.
- Use `gptme-eval --list` before guessing suite names or aliases.

## Model selection and comparison

Recommended benchmark baseline:

- `anthropic/claude-sonnet-4-6` is the documented default recommendation.

Common alternatives for comparison:

- `openai/gpt-5` and `openai/gpt-4o`
- `gemini/gemini-3-pro-preview`
- `deepseek/deepseek-chat` and `deepseek/deepseek-reasoner`
- OpenRouter variants of the same families when you need provider routing experiments

Comparison rules:

- Keep the suite, timeout, Docker mode, and `--parallel` value fixed while comparing models.
- Compare tool formats separately; a model can rank differently under `markdown`, `xml`, or native `tool` calling.
- When using OpenRouter for open-weight models, pin the provider if you need reproducible provider behavior.
- The `claude-code/<model>` prefix selects the Claude Code agent path for direct comparison against gptme; that path uses markdown-style tool formatting.

## Docker isolation

Prefer Docker for reproducibility and host isolation.

The CLI path is:

```bash
gptme-eval hello --model anthropic/claude-sonnet-4-6 --use-docker
```

What happens in Docker mode:

- the runner re-executes inside a container when not already inside Docker,
- the repository root is mounted into the container,
- the `eval_results/` tree is mounted so results survive the run,
- known provider credentials are forwarded through a temporary env file,
- the eval image is built if it is missing.

Docker constraints:

- Docker must be available and healthy on the host.
- Real model calls still need valid provider credentials and network access.
- The temporary env-file path is internal; the runtime should not expose it in logs.

Use Docker whenever you want to compare models, formats, or pass rates without host pollution.

## Timeouts, parallelism, and cost

- `--timeout` is the per-eval generation timeout in seconds.
- `--parallel` is the eval concurrency limit.
- Larger suites or slower models often need a longer timeout than the default.
- Real benchmark runs are cost-bearing; the sub-skill should not launch them without explicit authorization.
- Keep `--timeout` and `--parallel` identical when comparing runs, or the result table will be harder to interpret.
- `--no-lessons` is useful when you want a baseline with lesson injection disabled.
- `--user-context` is opt-in; leave it off when you want a clean benchmark comparison.

## Result layout

The CLI writes timestamped result directories under `eval_results/` unless `EVAL_RESULTS_DIR` points elsewhere.

Per run:

- `eval_results/<timestamp>/eval_results.csv`
- `eval_results/<timestamp>/eval_results.json` when `--json` is used
- `eval_results/<timestamp>/<model>/<format>/<test>/cases.csv`
- `eval_results/<timestamp>/<model>/<format>/<test>/gen_stdout.txt`
- `eval_results/<timestamp>/<model>/<format>/<test>/gen_stderr.txt`
- `eval_results/<timestamp>/<model>/<format>/<test>/run_stdout.txt`
- `eval_results/<timestamp>/<model>/<format>/<test>/run_stderr.txt`

The CSV contains the per-test summary fields used by the analysis tools:

- `Model`
- `Tool Format`
- `Test`
- `Passed`
- `Score`
- `Tool Calls`
- `Num Steps`
- `Tokens Input`
- `Tokens Output`
- `Tokens Total`
- `Cache Read Tokens`
- `Cache Creation Tokens`
- `Cache Hit Rate`
- `Cost USD`
- `Total Duration`
- `Generation Time`
- `Run Time`
- `Eval Time`
- `Commit Hash`
- `Log Dir`
- `Workspace Dir`

Use the result files as the source of truth for leaderboard and trend analysis. If a directory is missing the CSV, the analysis tools will not have enough data.

## SWE-bench high-level flow

Use `gptme-eval-swebench` for SWE-bench-style patch generation.

The common pattern is:

```bash
gptme-eval-swebench --info
gptme-eval-swebench -m anthropic/claude-sonnet-4-6 -i django__django-11099
gptme-eval-swebench -m anthropic/claude-sonnet-4-6 --resume --dataset princeton-nlp/SWE-bench_Lite
```

Recommended flow:

1. Inspect the dataset and instance IDs with `--info`.
2. Run one or more instances to produce `predictions.jsonl`.
3. Re-run with `--resume` when the predictions file already contains partial progress.
4. Use `--run-harness` only when you want the official SWE-bench evaluation and have Docker plus the benchmark extras available.

Important notes:

- The built-in SWE-bench summary is a lightweight heuristic, not the authoritative benchmark score.
- `--run-harness` requires Docker plus the benchmark dependencies.
- The harness command is external to the lightweight summary path.

## T-bench high-level flow

Use `gptme-eval-tbench` for Terminal-Bench runs.

Typical pattern:

```bash
gptme-eval-tbench --task hello-world
gptme-eval-tbench --model anthropic/claude-haiku-4-5 --task hello-world --task broken-python
```

Notes:

- The command checks `tb --version` before it runs the benchmark.
- The default dataset is `terminal-bench-core==head`; pin a specific dataset version if you want reproducible comparisons.
- The runner uses `gptme.eval.tbench.agent:GptmeAgent` under the hood.
- Results default to `runs/tbench`.
- Terminal-Bench support may require a Python environment that satisfies the project metadata marker for `terminal-bench` (`Python >=3.12`).

## Practical operating rule

When you need to prepare a run for another agent, fix these four things first:

1. suite or suite alias
2. model specification
3. tool format
4. isolation mode and timeout

Then use the bundled command builder script to print the exact command before you run anything.
