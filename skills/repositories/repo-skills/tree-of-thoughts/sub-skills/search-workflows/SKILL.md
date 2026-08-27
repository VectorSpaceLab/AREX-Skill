---
name: search-workflows
description: "Run and adapt tree-of-thoughts DFS/BFS search workflows with
  deterministic validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# search-workflows

Use this sub-skill when a task needs to run, adapt, or debug the `tree-of-thoughts` DFS or BFS orchestration classes. It covers search parameters, output parsing, autosave behavior, deterministic fake-agent smoke tests, and workflow-specific troubleshooting.

Do not use this sub-skill for model/provider setup details. If the task asks how to configure `TotAgent`, OpenAI credentials, or custom model callers, route that part to [agents-and-models](../agents-and-models/) and return here for DFS/BFS orchestration.

## Runtime assets

- [DFS and BFS workflow recipes](references/dfs-bfs-workflows.md) — constructors, safe recipes, output schemas, validation, autosave notes, and custom/fake agent patterns.
- [Workflow troubleshooting](references/troubleshooting.md) — empty/pruned outputs, evaluation ordering surprises, recursion growth, autosave paths, and real-model network/API-key failures.
- [Deterministic fake-agent smoke helper](scripts/fake_agent_search_smoke.py) — network-free checks for both DFS and BFS.

## Fast safe checks

Run from any working directory that has an installed `tree-of-thoughts` package and dependencies:

```bash
python /path/to/search-workflows/scripts/fake_agent_search_smoke.py --mode dfs --max-loops 1 --number-of-agents 2 --no-autosave
python /path/to/search-workflows/scripts/fake_agent_search_smoke.py --mode bfs --max-loops 1 --number-of-agents 2 --breadth-limit 2 --no-autosave
```

Expected signal: each command exits 0 and prints a JSON summary with the requested `mode`, generated-thought counts, parsed output keys, and a non-empty fake-agent call count.

## Operating rules

1. Import DFS from the root package: `from tree_of_thoughts import ToTDFSAgent`.
2. Import BFS from its module: `from tree_of_thoughts.bfs import BFSWithTotAgent`; it is not exported by the package root.
3. Give search agents an object with `.run(task) -> {"thought": str, "evaluation": float}`. The bundled fake script is the safest template.
4. Treat `.run(...)` results as JSON strings for both DFS and BFS; parse with `json.loads` before validating fields.
5. Keep `number_of_agents`, `max_loops`, and BFS `breadth_limit` small during smoke checks because both workflows can multiply calls quickly; start with `--max-loops 1 --number-of-agents 2`.
