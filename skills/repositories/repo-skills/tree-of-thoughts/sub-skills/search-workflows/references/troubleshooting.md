# Search workflow troubleshooting

Use this when DFS or BFS runs complete but produce surprising structure, empty results, excessive recursion, or file/network side effects.

## Import errors

### `BFSWithTotAgent` cannot be imported from `tree_of_thoughts`

Symptom:

```text
ImportError: cannot import name 'BFSWithTotAgent' from 'tree_of_thoughts'
```

Cause: BFS is not exported by the package root in 0.6.5.

Fix:

```python
from tree_of_thoughts.bfs import BFSWithTotAgent
```

DFS can still be imported from the root:

```python
from tree_of_thoughts import ToTDFSAgent
```

### Dependency import errors before any search starts

Symptom examples: import errors involving `swarms`, `swarm_models`, LangChain community modules, or provider packages.

Fixes:

1. Confirm the package and runtime dependencies are installed in the active Python environment.
2. If using a real `TotAgent`, route model/provider setup to `../agents-and-models/`.
3. For orchestration-only validation, run the fake-agent smoke script first; it avoids network calls but still imports the installed package.

## Empty or fully pruned DFS results

Symptom:

```json
{
  "final_thoughts": [],
  "pruned_branches": [...],
  "highest_rated_thought": null
}
```

Likely causes:

- `max_loops` is `0` or negative.
- The fake/custom agent returned evaluations at or below `prune_threshold`.
- The agent returned malformed dictionaries, so thoughts were not added as expected.
- `number_of_agents` is too small to generate any above-threshold branch.

Fixes:

- Start with `max_loops=1` or `2` and `number_of_agents=3`.
- Lower `prune_threshold`, for example from `0.5` to `0.3`.
- Assert every generated result has `thought` and numeric `evaluation`.
- Use the deterministic smoke script to prove the orchestration path:

```bash
python /path/to/search-workflows/scripts/fake_agent_search_smoke.py --mode dfs --max-loops 1 --number-of-agents 2 --no-autosave
```

## Unexpected evaluation ordering

### DFS best result appears last

DFS sorts generated and final thought lists ascending by `evaluation`. The highest-rated item is the last item in `final_thoughts`, and the JSON includes it as `highest_rated_thought`.

Use:

```python
best = data["highest_rated_thought"]
# or
best = max(data["final_thoughts"], key=lambda t: t["evaluation"])
```

Do not use `data["final_thoughts"][0]` as the best result.

### BFS selects high scores but returns `all_thoughts` ascending

BFS internally sorts state candidates descending to keep the best states under `breadth_limit`, but `run(...)` sorts `all_thoughts` ascending before returning JSON.

Use:

```python
best_logged = max(data["all_thoughts"], key=lambda t: t["evaluation"])
```

## Recursive or explosive runs

Symptoms:

- The process appears to recurse for a long time.
- The agent call count is much larger than expected.
- CPU usage spikes with many threads.
- Stateful fake agents produce confusing extra calls.

Causes:

- DFS expands every generated thought whose evaluation is greater than `prune_threshold` until `max_loops` stops recursion.
- BFS expands each retained state by `number_of_agents` and then re-runs the agent while selecting/generating the final answer.
- Both workflows use thread pools, so non-thread-safe fake agents can create nondeterministic counters or duplicate states.

Fixes:

- Keep first runs small: `max_loops=1` or `2`, `number_of_agents=2` or `3`, BFS `breadth_limit=1` or `2`.
- Raise DFS `prune_threshold` to reduce branches.
- Lower BFS `breadth_limit` to reduce retained states.
- Make fake agents thread-safe with a lock if they maintain counters.
- Validate call counts with the bundled smoke helper before introducing a real model.

## Autosave path surprises

### DFS created files in an unexpected directory

DFS `autosave_on=True` writes:

```text
tree_of_thoughts_runs/tree_of_thoughts_run{id}.json
```

The directory is relative to the current process working directory, not the skill directory.

Fixes:

- Use `autosave_on=False` during tests.
- Pass `--no-autosave` to the smoke script.
- If persistence is required, save `raw = dfs.run(task)` yourself to an explicit path.

### BFS did not autosave even though `autosave_on=True`

In 0.6.5, `BFSWithTotAgent` accepts `autosave_on`, but the save block in `run(...)` is disabled. Treat BFS autosave as unavailable and persist the returned JSON manually.

## Bad output shape from custom or real agents

Symptoms:

```text
KeyError: 'evaluation'
TypeError: 'NoneType' object is not subscriptable
TypeError: '<' not supported between instances
```

Likely causes:

- `agent.run(...)` returned a string instead of a dict.
- The dict lacks `thought` or `evaluation`.
- `evaluation` is a string such as `"0.8"` rather than a float.
- The agent sometimes returns `None`.

Fix with an adapter:

```python
class SafeAdapter:
    def __init__(self, base):
        self.base = base
        self.max_loops = getattr(base, "max_loops", None)

    def run(self, task):
        out = self.base.run(task)
        if isinstance(out, str):
            import ast
            out = ast.literal_eval(out)
        return {
            "thought": str(out["thought"]),
            "evaluation": float(out["evaluation"]),
        }
```

Prefer `ast.literal_eval` or JSON parsing for your own adapters. The package `TotAgent.run` uses `eval` internally, so only feed it model outputs you trust.

## API-key or network failures with real `TotAgent`

Symptoms:

- Missing `OPENAI_API_KEY` errors.
- Authentication or quota failures.
- Network timeouts.
- Provider-specific errors before a thought dict is returned.

Fixes:

1. Verify model setup through `../agents-and-models/`.
2. Keep `use_openai_caller=False` unless the OpenAI function-caller path is intentional.
3. Start with the fake-agent smoke script to separate search-orchestration issues from provider issues.
4. Once provider setup works, run with very small `max_loops` and `number_of_agents` to control cost.

## Quick triage matrix

| Symptom | First check | Usual fix |
| --- | --- | --- |
| `BFSWithTotAgent` import fails | Import path | Use `from tree_of_thoughts.bfs import BFSWithTotAgent`. |
| DFS best answer seems low quality | Ordering assumption | Read `highest_rated_thought` or use `max(...)`. |
| DFS output empty | `prune_threshold`, `max_loops` | Lower prune threshold; set `max_loops >= 1`; increase candidates. |
| BFS final is `None` | `breadth_limit`, `agent.run` returning `None` | Use `breadth_limit >= 1`; validate agent outputs. |
| Unexpected files appear | DFS autosave relative path | Disable autosave or save explicitly. |
| Run is expensive or slow | Loop/candidate sizes | Reduce `max_loops`, `number_of_agents`, and BFS `breadth_limit`. |
