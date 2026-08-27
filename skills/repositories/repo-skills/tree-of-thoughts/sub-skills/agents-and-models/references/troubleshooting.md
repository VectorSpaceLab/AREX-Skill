# Agents and model troubleshooting

Use this when model-agent setup fails before or during `TotAgent.run`. Fix these issues before debugging DFS/BFS traversal.

## Import failures

### `ModuleNotFoundError: No module named 'swarms'`

Cause: package dependencies are not installed in the active Python environment.

Check:

```bash
python - <<'PY'
import sys
print(sys.executable)
try:
    import swarms
    print("swarms import OK")
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

Fix:

```bash
python -m pip install -U tree-of-thoughts==0.6.5
```

Expected signal: `from tree_of_thoughts import TotAgent` imports without `ModuleNotFoundError`.

### LangChain community package errors

Symptoms may mention missing `langchain_community`, moved LangChain modules, or imports triggered by `swarms`/`swarm-models`.

Fix with the verified compatibility package:

```bash
python -m pip install -U langchain-community==0.3.31
```

Then retry:

```bash
python - <<'PY'
from tree_of_thoughts import TotAgent
from tree_of_thoughts.agent import Thought
print("import OK", TotAgent.__name__, list(getattr(Thought, "model_fields", getattr(Thought, "__fields__", {})).keys()))
PY
```

Expected signal: `import OK TotAgent ['thought', 'evaluation']` or equivalent field list.

### `ImportError` for `BFSWithTotAgent` from the root package

Cause: root package exports `TotAgent` and `ToTDFSAgent`, but not `BFSWithTotAgent`.

Fix:

```python
from tree_of_thoughts.bfs import BFSWithTotAgent
```

Expected signal: `BFSWithTotAgent.__name__ == "BFSWithTotAgent"`.

## Missing `OPENAI_API_KEY`

Symptoms:

- Authentication errors from OpenAI-compatible calls.
- Constructor appears to succeed but the first `run` fails.
- The default `OpenAIFunctionCaller` receives `openai_api_key=None`.

Fix for live OpenAI-backed runs:

```bash
export OPENAI_API_KEY="your_openai_api_key"
python - <<'PY'
import os
print("OPENAI_API_KEY set", bool(os.getenv("OPENAI_API_KEY")))
PY
```

Or create `.env` in the process working directory:

```bash
cat > .env <<'EOF'
OPENAI_API_KEY="your_openai_api_key"
EOF
```

Safer fix for offline checks: do not use the default caller. Use `use_openai_caller=False` with a custom model, or bypass the constructor for parser-only checks as shown in `references/api-reference.md`.

Expected signal: live runs authenticate, or offline smoke tests pass without reading `OPENAI_API_KEY`.

## Bad model output or `eval` failures

`TotAgent.run` converts the model response with Python `eval`. Common symptoms:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SyntaxError` | Extra prose, fenced Markdown, or incomplete dict text. | Return only `{'thought': '...', 'evaluation': 0.8}`. |
| `NameError: name 'true' is not defined` | JSON-only literal (`true`, `false`, `null`) reached Python `eval`. | Use Python-compatible literals or avoid booleans/null in the output. |
| `KeyError: 'evaluation'` or `KeyError: 'thought'` | Missing required key. | Force exact keys `thought` and `evaluation`. |
| `TypeError` during sorting/comparison | `evaluation` is a string, `None`, or non-numeric object. | Emit a numeric int/float, preferably 0.1-1.0. |
| Silent unsafe behavior risk | Untrusted text is executed by `eval`. | Validate with the checker and do not pass untrusted model output to package parsing. |

Preflight a sample:

```bash
python scripts/check_model_contract.py --sample-output '{"thought":"candidate","evaluation":0.8}'
```

Expected signal:

```text
OK: parsed dict with thought='candidate' evaluation=0.8
```

If this checker fails, fix the model prompt or adapter before invoking `TotAgent.run`.

## Custom model does not get called as expected

Symptoms:

- `TotAgent(use_openai_caller=False, model=...)` constructs but `run` fails inside `swarms.Agent`.
- The custom object returns a dict, but `TotAgent.run` expects text from `self.agent.run` and then evaluates it.
- The installed `swarms` version expects a different LLM interface than `__call__`.

Fix:

1. Ensure the final `agent.agent.run(task)` output is dict-like text, not an already-parsed dict.
2. For contract-only checks, bypass the constructor and inject a fake inner runner:

```python
from tree_of_thoughts import TotAgent

class FakeInnerAgent:
    def run(self, task):
        return repr({"thought": f"checked {task}", "evaluation": 0.7})

agent = object.__new__(TotAgent)
agent.agent = FakeInnerAgent()
print(agent.run("smoke"))
```

Expected signal: `{'thought': 'checked smoke', 'evaluation': 0.7}` prints as a Python dict.

## `swarms.Agent` constructor side effects and autosave files

`TotAgent` constructs a `swarms.Agent` during initialization. Verified constructor settings include verbose mode, `autosave=True`, and a `saved_state_path` derived from the id. Consequences:

- Local state files or workspace folders may appear even during short smoke runs.
- Logs may be noisy because verbose mode is enabled.
- Reusing implicit ids can make saved-state names confusing; pass an explicit short id for reproducible checks.
- Passing arbitrary `**kwargs` through `TotAgent` can conflict with hard-coded `swarms.Agent` keyword arguments if the same parameter name is supplied.

Safer patterns:

```python
# For parser-only checks: no constructor side effects.
agent = object.__new__(TotAgent)
agent.agent = FakeInnerAgent()

# For traversal wrappers: use their autosave_on=False option when available.
# Keep actual DFS/BFS parameter setup in search-workflows.
```

Expected signal: contract checks run without creating unexpected files; traversal smoke tests can keep autosave disabled.

## No-PyTorch warning or missing `torch`

The package metadata describes the project as PyTorch-related, but the verified model-agent import path and package requirements do not require importing `torch` for `TotAgent`, `Thought`, DFS, or BFS contract checks.

If a warning says PyTorch is absent but your task is only validating `TotAgent` output contracts, treat it as non-blocking. If your injected model backend needs PyTorch, install the backend-specific dependency separately and verify that model outside this sub-skill before connecting it to `TotAgent`.

Expected signal for this sub-skill: imports and `scripts/check_model_contract.py` pass even when PyTorch is not installed.

## Quick recovery sequence

From this sub-skill directory:

```bash
python -m pip install -U tree-of-thoughts==0.6.5 langchain-community==0.3.31
python scripts/check_model_contract.py --sample-output '{"thought":"smoke","evaluation":0.9}'
python - <<'PY'
from tree_of_thoughts import TotAgent

class FakeInnerAgent:
    def run(self, task):
        return repr({"thought": "smoke", "evaluation": 0.9})

agent = object.__new__(TotAgent)
agent.agent = FakeInnerAgent()
print(agent.run("task"))
PY
```

Expected signal: the checker prints `OK`, and the Python smoke prints a dict containing `thought` and numeric `evaluation`.
