---
name: planning-workflows
description: "Run AiZynthFinder retrosynthesis planning and one-step expansion
  through CLI, Python APIs, and optional notebook interfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Planning Workflows

Use this sub-skill when the task is to execute or script AiZynthFinder retrosynthesis planning, construct an `aizynthcli` command, call `AiZynthFinder` or `AiZynthExpander` from Python, debug target SMILES setup, checkpoint a batch run, or launch the optional notebook interface.

## Before You Run

- Confirm `aizynthfinder` is importable and the `aizynthcli` entry point is on `PATH`.
- Confirm a configuration file or config dictionary is available and points to usable stock, expansion-policy, and optional filter assets.
- If config/assets are missing, first use `../configuration-and-data/SKILL.md`.
- Decide whether `--smiles` is a literal single SMILES or a text file with one SMILES per row; multiprocessing requires a file.
- Decide which policy, filter, and stock keys to select at execution time; key names must match loaded config entries.
- Send output parsing, route images, scoring, clustering interpretation, and dataframe work to `../route-analysis/SKILL.md`.
- Send custom pre/post-processing implementations, plugins, custom stocks, or custom search classes to `../extension-and-development/SKILL.md`.

## Workflow Map

- For safe CLI command construction, use `scripts/build_aizynthcli_command.py` and then run the printed command in the intended environment.
- For CLI behavior, flags, defaults, and command patterns, read `references/cli-reference.md`.
- For end-to-end single, batch, checkpointed, API, one-step expansion, and notebook recipes, read `references/workflows.md`.
- For public API signatures, lifecycle ordering, and return-object notes, read `references/api-reference.md`.
- For concrete failure symptoms and recoveries, read `references/troubleshooting.md`.

## Quick Routes

- Single CLI target: build `aizynthcli --config CONFIG --smiles SMILES`, optionally with `--output trees.json`.
- Batch CLI targets: build `aizynthcli --config CONFIG --smiles smiles.txt --output output.json.gz`, optionally with `--checkpoint checkpoint.json.gz`.
- Parallel batch: use `--nproc N` only when `--smiles` names an existing file.
- Python planning: instantiate `AiZynthFinder`, select stock/policy/filter keys, set `target_smiles`, run `prepare_tree()`, `tree_search(show_progress=False)`, `build_routes()`, then call `extract_statistics()` and `stock_info()`.
- One-step expansion: instantiate `AiZynthExpander`, select policies and optional filters, then call `do_expansion(smiles, return_n=5, filter_func=None)`.
- GUI/notebook: use `aizynthapp --config CONFIG` or create an `AiZynthApp` inside Jupyter only when an interactive notebook environment is available.
