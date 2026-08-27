# tree-of-thoughts package overview

Read this when you need a compact map of the repository's public capabilities before selecting a sub-skill.

## Purpose

`tree-of-thoughts` is a Python package for orchestrating Tree-of-Thoughts-style reasoning. It wraps a model-facing `TotAgent` and provides DFS and BFS search classes that repeatedly ask an agent for candidate thoughts with numeric evaluations.

The package is useful for:

- Building a model-backed `TotAgent` that returns a structured `Thought` with `thought` and `evaluation` fields.
- Running DFS with pruning through `ToTDFSAgent`.
- Running BFS with a breadth limit through `BFSWithTotAgent`.
- Experimenting with prompt templates for multi-expert/tree-of-thought reasoning.

## Install and import

Use Python 3.10+.

```bash
python -m pip install -U tree-of-thoughts==0.6.5
# Compatibility repair for environments where swarm-models imports LangChain community modules:
python -m pip install -U langchain-community==0.3.31
```

Minimal import check:

```bash
python - <<'PY'
from tree_of_thoughts import TotAgent, ToTDFSAgent
from tree_of_thoughts.bfs import BFSWithTotAgent
print(TotAgent.__name__, ToTDFSAgent.__name__, BFSWithTotAgent.__name__)
PY
```

Expected signal: `TotAgent ToTDFSAgent BFSWithTotAgent`.

## Public routes

| Task | Use |
|---|---|
| Configure the model caller, validate output shape, or debug `OPENAI_API_KEY`/dependency imports | `sub-skills/agents-and-models/` |
| Run DFS or BFS, choose search parameters, parse JSON outputs, or smoke-test orchestration offline | `sub-skills/search-workflows/` |
| Check whether an environment can import package modules | `scripts/check_tree_of_thoughts_env.py` |
| Understand stale scripts, release notes, and repository maintenance caveats | `references/maintainer-notes.md` |

## Important implementation facts

- Root `tree_of_thoughts` exports `TotAgent` and `ToTDFSAgent`.
- `BFSWithTotAgent` exists in `tree_of_thoughts.bfs`; import it from that module.
- `TotAgent.run(task)` delegates to the underlying `swarms.Agent` and converts the model output string to a Python dict using `eval`. Validate and constrain model output before trusting it.
- DFS and BFS expect an agent object whose `.run(task)` returns a dict with `thought` and numeric `evaluation`.
- Both DFS and BFS `.run(...)` methods return JSON strings, not Python dicts.
- The default OpenAI-backed `TotAgent` path needs `OPENAI_API_KEY` and external service access; deterministic fake/custom agents are better for verification and CI.

## Prompt templates

The repository includes prompt examples for collaborative multi-expert reasoning. Use them as inspiration for model prompts, but keep generated outputs constrained to the `Thought` contract when the output will feed DFS/BFS.

A safe prompt pattern should explicitly require output shaped like:

```python
{"thought": "candidate next step", "evaluation": 0.82}
```

When the model is not guaranteed to emit a parseable Python literal/dict-like string, validate it first with `sub-skills/agents-and-models/scripts/check_model_contract.py`.
