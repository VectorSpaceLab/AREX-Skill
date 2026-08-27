---
name: tree-of-thoughts
description: "Use the tree-of-thoughts Python package to configure TotAgent
  model callers and run DFS/BFS Tree-of-Thoughts reasoning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# tree-of-thoughts

Use this repo skill when a task involves the `tree-of-thoughts` / `tree_of_thoughts` Python package, `TotAgent`, `ToTDFSAgent`, `BFSWithTotAgent`, Tree-of-Thoughts prompt orchestration, thought/evaluation output contracts, DFS pruning, BFS breadth limits, or package-specific install/import troubleshooting.

Do not use this skill for the Princeton reference implementation unless the user is specifically porting concepts into this package. Do not use it for generic prompt engineering with no package/API work.

## Fast orientation

- Package distribution: `tree-of-thoughts`.
- Import package: `tree_of_thoughts`.
- Verified source version: `0.6.5`.
- Python: use Python 3.10+.
- Root exports: `TotAgent`, `ToTDFSAgent`.
- BFS class: import `BFSWithTotAgent` from `tree_of_thoughts.bfs`.
- Default real model path: requires `OPENAI_API_KEY` and external service access.
- Safe verification path: use deterministic fake/custom agents that return `{"thought": str, "evaluation": float}`.

## Install and import check

```bash
python -m pip install -U tree-of-thoughts==0.6.5
# If imports fail through swarm-models/LangChain split packages:
python -m pip install -U langchain-community==0.3.31
```

Minimal import probe:

```bash
python - <<'PY'
from tree_of_thoughts import TotAgent, ToTDFSAgent
from tree_of_thoughts.bfs import BFSWithTotAgent
print(TotAgent.__name__, ToTDFSAgent.__name__, BFSWithTotAgent.__name__)
PY
```

Expected signal: `TotAgent ToTDFSAgent BFSWithTotAgent`.

For a fuller no-network check, run [scripts/check_tree_of_thoughts_env.py](scripts/check_tree_of_thoughts_env.py); it verifies package metadata, public imports, and the root/BFS API split without calling a provider.

## Route map

| If the task asks about... | Read |
|---|---|
| Installing/importing the package, package purpose, public API map, prompt-template caveats | [references/package-overview.md](references/package-overview.md) |
| Configuring `TotAgent`, choosing OpenAI vs custom/fake model callers, validating `Thought` outputs, or handling `OPENAI_API_KEY` | [sub-skills/agents-and-models/SKILL.md](sub-skills/agents-and-models/SKILL.md) |
| Running DFS, running BFS, choosing thresholds/loop/breadth settings, parsing JSON results, autosave behavior, or offline smoke tests | [sub-skills/search-workflows/SKILL.md](sub-skills/search-workflows/SKILL.md) |
| Import errors, dependency compatibility, unsafe parsing, real-model failures, or autosave surprises | [references/troubleshooting.md](references/troubleshooting.md) |
| Repository scripts, packaging/release facts, stale maintainer automation, or source maintenance caveats | [references/maintainer-notes.md](references/maintainer-notes.md) |
| Checking whether this skill matches a checkout/commit | [references/repo-provenance.md](references/repo-provenance.md) |

## Operating workflow

1. Start with the import probe above or `scripts/check_tree_of_thoughts_env.py --json`.
2. If model setup is involved, enter `agents-and-models` first. Validate the model output contract before passing model results into search.
3. If traversal is involved, enter `search-workflows`. Keep `max_loops`, `number_of_agents`, and BFS `breadth_limit` small until the deterministic fake-agent helper passes.
4. Parse DFS/BFS `.run(...)` return values with `json.loads`; both return JSON strings.
5. For live OpenAI-backed experiments, confirm `OPENAI_API_KEY` and network/provider permission before running `TotAgent(use_openai_caller=True)`.

## Safety and correctness notes

- `TotAgent.run` converts model text to a dict using Python `eval`; never treat arbitrary or user-controlled model output as safe.
- The DFS implementation sorts thoughts ascending by evaluation; the highest-rated final thought is the last item and is also exposed as `highest_rated_thought`.
- DFS autosave writes under `tree_of_thoughts_runs/` relative to the process working directory when `autosave_on=True`; disable autosave for tests.
- Some repository scripts are stale or destructive; do not run original source scripts as runtime helpers unless a maintainer task explicitly calls for updating them.
