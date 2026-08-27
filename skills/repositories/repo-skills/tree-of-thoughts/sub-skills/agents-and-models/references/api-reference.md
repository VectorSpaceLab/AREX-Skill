# Agents and model API reference

This reference covers the model-facing layer only. Use it before any DFS/BFS workflow so the generated thoughts are predictable and parseable.

## Install and import expectations

Use Python 3.10+ and install the package plus its model-agent dependencies. A compatible import set observed for `tree-of-thoughts` 0.6.5 includes `langchain-community==0.3.31`, which is needed by current `swarms`/LangChain split packages in some environments.

```bash
python -m pip install -U tree-of-thoughts==0.6.5 langchain-community==0.3.31
```

When working from a local checkout instead of the wheel:

```bash
python -m pip install -e .
python -m pip install -U langchain-community==0.3.31
```

Expected import probe:

```bash
python - <<'PY'
from tree_of_thoughts import TotAgent, ToTDFSAgent
from tree_of_thoughts.agent import Thought, string_to_dict
from tree_of_thoughts.bfs import BFSWithTotAgent

fields = getattr(Thought, "model_fields", getattr(Thought, "__fields__", {}))
print("TotAgent", TotAgent.__name__)
print("ToTDFSAgent", ToTDFSAgent.__name__)
print("BFSWithTotAgent", BFSWithTotAgent.__name__)
print("Thought fields", list(fields.keys()))
print("dict parser", string_to_dict("{'thought': 'ok', 'evaluation': 0.7}"))
PY
```

Expected signal: imports succeed; `Thought fields` includes exactly `thought` and `evaluation`; the parser prints a dict with those keys.

Public import notes:

- Root package exports `TotAgent` and `ToTDFSAgent`.
- `BFSWithTotAgent` is available from `tree_of_thoughts.bfs`; do not expect it in root `__all__`.
- Native dependency names include `swarms`, `swarm-models`, `pydantic`, `loguru`, and `python-dotenv`.

## Environment variables and model selection

The agent modules load `.env` via `python-dotenv`. For the default OpenAI-backed path, create a `.env` in the process working directory or export variables before running Python:

```bash
cat > .env <<'EOF'
OPENAI_API_KEY="your_openai_api_key"
EOF
```

Use `TotAgent(use_openai_caller=True)` only when external service access is allowed and `OPENAI_API_KEY` is present. For offline tests, CI, deterministic smoke checks, or untrusted prompt experiments, use `use_openai_caller=False` and inject or replace the runner with a fake/custom object that returns the exact thought contract.

## Verified API surface

### `Thought`

`Thought` is a Pydantic model with these fields:

| Field | Type | Contract |
| --- | --- | --- |
| `thought` | `str` | The generated step, state, or candidate answer text. |
| `evaluation` | optional `float` | Quality score, intended to be numeric from `0.1` to `1.0`. DFS/BFS code compares this value numerically. |

### `TotAgent`

Constructor signature verified from source:

```python
TotAgent(
    id: str = uuid.uuid4().hex,
    max_loops: int = None,
    use_openai_caller: bool = True,
    model: Optional[Any] = None,
    *args,
    **kwargs,
)
```

Run signature:

```python
TotAgent.run(task: Any) -> dict
```

Runtime behavior:

1. Constructor stores `id`, `max_loops`, and `model`.
2. If `use_openai_caller=True`, it replaces `model` with `OpenAIFunctionCaller(system_prompt=..., base_model=Thought, openai_api_key=os.getenv("OPENAI_API_KEY"), max_tokens=3000, ...)`.
3. It constructs a `swarms.Agent` with `llm=self.model`, `max_loops=1`, verbose mode, autosave enabled, and a `saved_state_path` derived from the agent id.
4. `run(task)` calls `self.agent.run(task)` and then parses that text with `string_to_dict`, which uses Python `eval`.

The returned value from `TotAgent.run` must be a Python dict shaped like:

```python
{"thought": "candidate reasoning step", "evaluation": 0.82}
```

### DFS/BFS-facing output keys

Traversal wrappers assume exact keys:

- `thought`: string used as the next state.
- `evaluation`: numeric value used for sorting, pruning, and final selection.

Known run return types:

- `TotAgent.run(...)` returns a Python `dict`.
- `ToTDFSAgent.run(...)` returns a JSON string with `final_thoughts`, `pruned_branches`, and `highest_rated_thought`.
- `BFSWithTotAgent.run(...)` returns a JSON string with `all_thoughts` and `final_thought`.

Keep DFS/BFS traversal usage in the search-workflows sub-skill; this section only states the model contract those workflows consume.

## Model-output contract

The `TotAgent` parser expects model output to be dict-like text, not prose or Markdown. Safe examples:

```text
{'thought': 'Try grouping the numbers into two products.', 'evaluation': 0.78}
{"thought": "Use subtraction before division.", "evaluation": 0.64}
```

Reject or regenerate outputs like prose wrappers or fenced Markdown:

```text
Here is my thought: {'thought': 'x', 'evaluation': 0.8}
```

````text
```json
{"thought": "x", "evaluation": "high"}
```
````

Why: `string_to_dict` calls `eval(model_text)`. Extra prose, fenced Markdown, non-numeric evaluations, missing keys, or JSON-only literals such as `true`, `false`, and `null` can fail or produce objects that DFS/BFS cannot compare.

Security caveat: because package parsing uses Python `eval`, do not pass untrusted model text directly to `TotAgent.run`. Constrain prompts and models to dict-only output, validate samples first, and prefer fake/deterministic runners for tests. The bundled checker uses safe parsing and does not execute sample text.

Validate a sample from this sub-skill directory:

```bash
python scripts/check_model_contract.py --sample-output '{"thought":"try factorization","evaluation":0.82}'
```

Expected signal:

```text
OK: parsed dict with thought=<...> evaluation=0.82
```

## Safe fake runner for parser-only checks

This pattern tests `TotAgent.run` parsing without constructing the external OpenAI caller and without relying on a live `swarms.Agent` run. It intentionally bypasses the constructor because the constructor has side effects and may require model dependencies even when no network call is desired.

```python
from tree_of_thoughts import TotAgent

class FakeInnerAgent:
    def run(self, task):
        return repr({
            "thought": f"deterministic step for {task}",
            "evaluation": 0.75,
        })

agent = object.__new__(TotAgent)
agent.agent = FakeInnerAgent()
agent.max_loops = 1

result = agent.run("smoke task")
assert result["thought"].startswith("deterministic step")
assert isinstance(result["evaluation"], float)
print(result)
```

Expected signal: a dict prints and assertions pass without requiring `OPENAI_API_KEY`.

## Injecting a custom model into `TotAgent`

Use this only when your custom object satisfies the `swarms.Agent` LLM interface used by the installed `swarms` version. The final text returned by `TotAgent.agent.run(...)` still must match the dict-like output contract.

```python
from tree_of_thoughts import TotAgent

class DictTextModel:
    def __call__(self, *args, **kwargs):
        return repr({"thought": "custom model step", "evaluation": 0.9})

agent = TotAgent(
    use_openai_caller=False,
    model=DictTextModel(),
    id="custom-model-smoke",
)

# If the installed swarms Agent does not call your model object directly,
# replace agent.agent with a small object exposing run(task) -> dict-like text.
```

Expected signal for a correct integration: `agent.agent.run(task)` eventually returns text like `{'thought': '...', 'evaluation': 0.9}`, and `agent.run(task)` returns a dict.

## Deterministic adapter for downstream DFS/BFS smoke checks

For offline traversal smoke tests, the DFS/BFS constructors only need an object exposing `run(state) -> dict` with the same keys. Use an adapter like this and route the traversal setup itself to search-workflows:

```python
class SequenceThoughtAgent:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1
        return {
            "thought": f"state-{self.calls} from {state}",
            "evaluation": 0.6 + min(self.calls, 3) * 0.1,
        }

fake_agent = SequenceThoughtAgent()
first = fake_agent.run("root")
assert set(first) == {"thought", "evaluation"}
assert isinstance(first["evaluation"], float)
```

Expected signal: repeated calls produce deterministic dicts with numeric scores, allowing traversal code to test sorting/pruning without network or API keys.

## Preflight checklist

Before handing off to search-workflows:

1. Import `TotAgent`, `Thought`, and any needed traversal wrapper.
2. Decide model path: OpenAI-backed only with `OPENAI_API_KEY`; otherwise fake/custom.
3. Validate a representative model text with `scripts/check_model_contract.py`.
4. Confirm `agent.run("small task")` returns a dict with `thought` and numeric `evaluation`.
5. Avoid using raw untrusted model output with the package parser.
