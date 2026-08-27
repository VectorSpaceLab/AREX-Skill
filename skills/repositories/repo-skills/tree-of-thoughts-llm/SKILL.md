---
name: tree-of-thoughts-llm
description: "Routes Tree of Thoughts workflows for game24, coherent passage
  generation, and mini-crossword solving, with shared installation and execution
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tree of Thoughts LLM

Use this skill for the Princeton NLP Tree of Thoughts repository and package.
It focuses on the bundled `tot` package, the shared runner, and the three
public task modes: arithmetic puzzles, coherent text generation, and mini
crossword solving.

## Fast start

- Install from PyPI: `pip install tree-of-thoughts-llm`
- Install from a checkout: `pip install -e .`
- Required runtime setting: `OPENAI_API_KEY`
- Optional proxy/base URL: `OPENAI_API_BASE`
- Smoke check: `python scripts/check_install.py`

## Choose a route

- `sub-skills/game24/` for 24-game arithmetic trajectories, ToT BFS, and
  naive sampling baselines.
- `sub-skills/text/` for coherent passage generation, sample/vote runs, and
  GPT-based coherency scoring.
- `sub-skills/crosswords/` for 5x5 mini crosswords, naive sampling, and the
  notebook-derived DFS search workflow.

## Shared runtime helper

- `scripts/run_tot.py` is the bundled runner that mirrors the repository
  runner interface and writes JSON logs under `./logs/` relative to the launch
  directory.
- `scripts/check_install.py` confirms the runtime package install, public
  metadata, and the three task constructors from the active environment.

## What this skill does not do

- It does not depend on the original checkout being present at runtime.
- It does not bundle private API keys, proxies, or machine-specific paths.
- It does not run the paper experiments automatically; use the route-specific
  sub-skill scripts or the shared runner with explicit task arguments.

## Shared prerequisites

The package is pure Python, but the workflows call the OpenAI Chat Completions
API. Expect the following before running any task mode:

- A valid OpenAI key in `OPENAI_API_KEY`.
- A reachable API endpoint, optionally overridden with `OPENAI_API_BASE`.
- Network access to the chosen backend.
- The runtime package installed with its pinned dependencies.

## Read next

- `references/workflows.md` for the shared ToT execution model and extension
  notes.
- `references/cli-reference.md` for the bundled runner flags and example
  commands.
- `references/api-reference.md` for verified package functions and task
  classes.
- `references/troubleshooting.md` for install, import, API, and parsing
  failures.
- `references/repo-provenance.md` before refreshing this skill from a newer
  checkout.
