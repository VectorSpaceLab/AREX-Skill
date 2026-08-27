---
name: evals-and-benchmarks
description: "Run and analyze gptme eval suites, benchmark outputs,
  SWE-bench/T-bench flows, Docker-isolated eval runs, and leaderboard/trend
  results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evals-and-benchmarks

Use this sub-skill when the task is about gptme eval suites, benchmark command construction, leaderboard/result processing, pass-rate interpretation, SWE-bench, T-bench, Docker-isolated runs, or comparing models and tool formats.

Route away when the task is mainly about:

- ordinary package tests, linting, type checking, docs, releases, or repo maintenance: use the repo-development sub-skill.
- provider credentials, auth setup, or model routing outside eval execution: use configuration-and-providers.
- browser/computer-use implementation, custom tools, plugins, or MCP behavior outside eval suites: use tools-and-extensibility.
- `gptme-server`, Web UI, ACP, or TUI: use the server/protocols sub-skill.

## Read first

- [references/eval-workflows.md](references/eval-workflows.md) for suite aliases, model and tool-format selection, `--use-docker`, `all`/`all-practical`, raw result locations, and SWE-bench/T-bench flow notes.
- [references/result-analysis.md](references/result-analysis.md) for leaderboard formats, per-test and trend outputs, pass-rate gates, and how to read local `eval_results.csv` files.
- [references/troubleshooting.md](references/troubleshooting.md) for eval-extra import failures, missing credentials, Docker/harness issues, timeouts, and result-directory problems.

## Safe helpers

- [scripts/check_eval_command.py](scripts/check_eval_command.py) builds a dry-run `gptme-eval` command for suites, models, formats, Docker, timeout, and parallel settings without executing anything.
- [scripts/summarize_eval_results.py](scripts/summarize_eval_results.py) summarizes local `eval_results.csv` files and tiny CSV fixtures without running model calls.

## Fast operating checklist

1. Prefer `gptme-eval --list` when you need the authoritative suite inventory.
2. Use explicit model prefixes and an explicit tool format when comparing runs: `model@format` or `--tool-format`.
3. Prefer `--use-docker` for isolation and reproducibility; treat real benchmark runs as cost-bearing and do not launch them unless the user authorized that spend.
4. Read existing CSV results before rerunning a benchmark; the bundled summarizer is for local files only.
5. For SWE-bench and T-bench, follow the dedicated flow notes in the bundled references instead of ad hoc harness commands.
