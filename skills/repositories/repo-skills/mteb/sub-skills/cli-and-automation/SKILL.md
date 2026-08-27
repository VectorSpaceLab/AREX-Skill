---
name: cli-and-automation
description: "Use the MTEB console script for safe CLI workflows, shell
  automation, command/API mapping, and CLI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MTEB CLI And Automation

Use this sub-skill when the user wants to drive MTEB through the `mteb` console command, inspect available tasks or benchmarks from a shell, generate model-card metadata from existing result caches, launch the local leaderboard, or build automation around these commands.

## Route By Intent

- **Run evaluations from a terminal**: Use `mteb run` patterns in `references/cli-reference.md`, then route to `../evaluation-workflows/SKILL.md` for evaluation semantics such as model loading, result caching, overwrite behavior, and prediction output.
- **List or filter tasks and benchmarks**: Use `mteb available-tasks` and `mteb available-benchmarks`, then route to `../tasks-and-benchmarks/SKILL.md` for task names, language filters, task types, benchmark selection, private/beta/superseded filtering, and Python-side `get_tasks` usage.
- **Generate model-card metadata**: Use the metadata command guidance in `references/cli-reference.md`, then route to `../results-and-leaderboard/SKILL.md` for result-cache layout, model-card/frontmatter expectations, leaderboard cache interpretation, and publishing considerations.
- **Launch or debug the leaderboard**: Use `mteb leaderboard` command guidance here, then route to `../results-and-leaderboard/SKILL.md` for result discovery, cache rebuild choices, and score display issues.
- **Write scripts or CI checks**: Use `references/automation-patterns.md` and the bundled `scripts/check_mteb_cli.py` helper to validate command availability without running benchmarks.
- **Fix CLI failures**: Start with `references/troubleshooting.md`, then route to the sibling sub-skill that owns the failing domain when the issue is task selection, evaluation behavior, result layout, or leaderboard display.

## Command Surface

The installed `mteb` console entry point exposes these core commands:

- `mteb run`: Loads a model with `mteb.get_model(...)`, selects tasks or benchmarks, then calls `mteb.evaluate(...)`.
- `mteb available-tasks`: Lists task inventory using task-selection filters.
- `mteb available-benchmarks`: Lists benchmark inventory, optionally filtered by benchmark names.
- `mteb create-model-results`: Generates or updates model-card metadata from cached MTEB results. Some docs or older workflows may call this workflow `create-meta`; always confirm the installed command with `mteb --help`.
- `mteb leaderboard`: Launches a local leaderboard app over a `ResultCache`; it may require optional leaderboard dependencies.

Always prefer `mteb <command> --help` over memory when scripting against a specific environment, because command names and aliases can differ across MTEB releases.

## Safe Defaults

- Use `mteb --help` and `mteb <command> --help` for validation; these commands should not download datasets or run models.
- Make output paths explicit with `--output-folder`, `--results-folder`, `--output-path`, and `--cache-path` so automation does not accidentally mix runs.
- Prefer `--overwrite-strategy only-missing` for resumable evaluations and `--overwrite-strategy always` only for deliberate reruns.
- Prefer `--prediction-folder` over deprecated `--save_predictions`.
- Treat benchmark selection as exclusive: when `--benchmarks` is used with `--tasks`, `--languages`, `--task-types`, `--categories`, or `--eval-splits`, MTEB warns that the task filters are ignored.

## Bundled Helper

Run the bundled checker before automating a machine or CI image:

```bash
python sub-skills/cli-and-automation/scripts/check_mteb_cli.py --subcommands run available-tasks available-benchmarks create-model-results leaderboard
```

The helper executes only help commands by default and reports missing subcommands or required option markers. It does not run evaluations, download datasets, launch the leaderboard server, or write result files unless you explicitly wrap it in broader automation.
