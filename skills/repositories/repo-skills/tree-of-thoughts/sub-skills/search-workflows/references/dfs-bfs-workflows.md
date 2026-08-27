# DFS and BFS workflow recipes

This reference is for `tree-of-thoughts` 0.6.5 search orchestration. It assumes model setup is already handled. For `TotAgent`, OpenAI credentials, or custom model callers, route to `../agents-and-models/`.

## Shared thought contract

Both search classes call an agent object repeatedly. The agent must provide:

```python
class MyAgent:
    max_loops = None  # DFS assigns this attribute during construction.

    def run(self, task):
        return {"thought": "next candidate state", "evaluation": 0.82}
```

Requirements:

- `thought` must be a string or string-like next state.
- `evaluation` must be numeric; higher means better for BFS selection and for final DFS ranking.
- Return dictionaries directly when using a fake/custom search agent. `TotAgent.run` itself returns a dictionary by evaluating the underlying model output, but model setup details belong in `../agents-and-models/`.
- Both workflow `.run(...)` methods return JSON strings. Always parse them before validation:

```python
import json

data = json.loads(search_agent.run(task))
```

## DFS: `ToTDFSAgent`

Import:

```python
from tree_of_thoughts import ToTDFSAgent
```

Constructor:

```python
dfs_agent = ToTDFSAgent(
    agent=my_agent,
    threshold=0.8,
    max_loops=2,
    prune_threshold=0.5,
    number_of_agents=3,
    autosave_on=False,
    id="short-run-id",
)
```

Parameters:

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `agent` | Object whose `run(task)` returns `{"thought", "evaluation"}`. | Use a deterministic fake for smoke tests; use a configured `TotAgent` only when external model calls are intended. |
| `threshold` | Early-return threshold checked against recursive DFS results. | Use `0.7`-`0.9` for high-quality answers, but still inspect `highest_rated_thought` because short runs may not trigger early returns. |
| `max_loops` | Maximum recursion depth; DFS also assigns `agent.max_loops = max_loops`. | Start at `1` or `2`. Calls can grow quickly with `number_of_agents`. |
| `prune_threshold` | Thoughts with `evaluation <= prune_threshold` are recorded as pruned and not expanded. | Lower it when every branch is pruned; raise it to reduce exploration. |
| `number_of_agents` | Number of candidate thoughts generated per state with a `ThreadPoolExecutor`. | Keep small. Use thread-safe fake agents if maintaining counters. |
| `autosave_on` | If true, writes the returned JSON to `tree_of_thoughts_runs/tree_of_thoughts_run{id}.json`. | Disable for tests with `False` or the smoke helper's `--no-autosave`. Autosave path is relative to the current process working directory. |
| `id` | Identifier included in the DFS autosave filename. | Set an explicit short id for reproducible filenames. |

Run and parse:

```python
raw = dfs_agent.run("Use arithmetic to make 24 from 4, 7, 8, 8.")
data = json.loads(raw)
```

DFS output schema:

```json
{
  "final_thoughts": [
    {"thought": "candidate text", "evaluation": 0.82}
  ],
  "pruned_branches": [
    {
      "thought": "candidate text",
      "evaluation": 0.32,
      "reason": "Evaluation score below threshold"
    }
  ],
  "highest_rated_thought": {"thought": "candidate text", "evaluation": 0.91}
}
```

Validation checklist:

1. `json.loads(raw)` succeeds.
2. `final_thoughts` and `pruned_branches` are lists.
3. Every thought dict has `thought` and numeric `evaluation`.
4. `highest_rated_thought` is either `None` or equals the last item after sorting `final_thoughts` by ascending `evaluation`.
5. If `final_thoughts` is empty, check whether `max_loops <= 0`, `number_of_agents <= 0`, or all evaluations were at or below `prune_threshold`.

Important DFS ordering caveat: generated thoughts are sorted with `reverse=False` before expansion, and final thoughts are also sorted ascending. The highest-rated DFS thought is therefore the last item, not the first. Do not assume the traversal expands the best candidate first.

## Adapted DFS recipe without OpenAI by default

Use this pattern when adapting the README-style arithmetic example but avoiding network calls:

```python
import json
from tree_of_thoughts import ToTDFSAgent

class ArithmeticFakeAgent:
    max_loops = None

    def __init__(self):
        self.calls = 0

    def run(self, task):
        self.calls += 1
        candidates = [
            {"thought": "Try (8 - 4) * (7 - 1) = 24", "evaluation": 0.88},
            {"thought": "Try 8 * 4 - 7 - 1 = 24", "evaluation": 0.52},
            {"thought": "Unhelpful branch", "evaluation": 0.25},
        ]
        return candidates[(self.calls - 1) % len(candidates)]

agent = ArithmeticFakeAgent()
dfs = ToTDFSAgent(
    agent=agent,
    threshold=0.8,
    max_loops=2,
    prune_threshold=0.5,
    number_of_agents=3,
    autosave_on=False,
    id="arithmetic-fake",
)
result = json.loads(dfs.run("Use 1, 4, 7, 8 to make 24."))
assert result["highest_rated_thought"] is not None
print(result["highest_rated_thought"])
```

Switch to a real `TotAgent` only after model setup is verified through `../agents-and-models/`.

## BFS: `BFSWithTotAgent`

Import from the module, not the root package:

```python
from tree_of_thoughts.bfs import BFSWithTotAgent
```

Constructor:

```python
bfs_agent = BFSWithTotAgent(
    agent=my_agent,
    max_loops=2,
    breadth_limit=2,
    number_of_agents=3,
    autosave_on=False,
    id="short-bfs-run",
)
```

Parameters:

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `agent` | Object whose `run(task)` returns `{"thought", "evaluation"}`. | Fake/custom agents work; no `TotAgent` instance is required if the contract is satisfied. |
| `max_loops` | Number of BFS expansion levels. | Start with `1` or `2`; each state expands by `number_of_agents`. |
| `breadth_limit` | Number of best states kept after each level. | Use `1` for greedy behavior; use `2`-`3` for broader exploration. `0` can produce no final thought. |
| `number_of_agents` | Number of candidate thoughts generated per current state. | Total calls can grow as `states * number_of_agents`, plus final-answer re-evaluation calls. |
| `autosave_on` | Constructor accepts it. In 0.6.5, BFS does not write an autosave file because the save block is disabled. | Persist the returned JSON yourself if needed. |
| `id` | Stored on the BFS instance. | Useful for your own filenames if you save results. |

Run and parse:

```python
raw = bfs_agent.run("Select the best concise answer path.")
data = json.loads(raw)
```

BFS output schema:

```json
{
  "all_thoughts": [
    {"thought": "candidate text", "evaluation": 0.58}
  ],
  "final_thought": {"thought": "selected final candidate", "evaluation": 0.82}
}
```

Validation checklist:

1. `json.loads(raw)` succeeds.
2. `all_thoughts` is a list sorted ascending by `evaluation` in the returned JSON.
3. `final_thought` is either `None` or has `thought` and numeric `evaluation`.
4. If `final_thought` is `None`, inspect `breadth_limit`, `max_loops`, and whether the agent returned `None`.
5. Remember that BFS re-runs `agent.run(...)` while selecting and generating the final answer, so stateful agents may see extra calls beyond expansion calls.

Important BFS ordering caveat: BFS selects the best states internally with descending evaluations, but the returned `all_thoughts` list is sorted ascending. Use `max(data["all_thoughts"], key=lambda t: t["evaluation"])` when you need the best logged candidate.

## Smoke-test commands

From any working directory with the package installed, run the bundled deterministic helper:

```bash
python /path/to/search-workflows/scripts/fake_agent_search_smoke.py --mode dfs --max-loops 1 --number-of-agents 2 --no-autosave
python /path/to/search-workflows/scripts/fake_agent_search_smoke.py --mode bfs --max-loops 1 --number-of-agents 2 --breadth-limit 2 --no-autosave
```

Expected DFS summary fields include `final_thoughts_count`, `pruned_branches_count`, `highest_rated_thought`, `fake_agent_calls`, and `autosave_enabled`.

Expected BFS summary fields include `all_thoughts_count`, `final_thought`, `fake_agent_calls`, `breadth_limit`, and `autosave_enabled`.

## Persisting results safely

DFS can autosave relative to the current working directory. BFS 0.6.5 returns JSON but does not autosave. A portable explicit save pattern is:

```python
from pathlib import Path

out = Path("tree_of_thoughts_runs")
out.mkdir(exist_ok=True)
out.joinpath("my_search_result.json").write_text(raw, encoding="utf-8")
```

Use explicit paths in automation instead of relying on implicit current-working-directory behavior.
