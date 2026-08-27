# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AttributeError` when assigning `model.agents` | `model.agents` is reserved for Mesa's live registry | Use a different attribute name for custom storage, and create/remove agents with `Agent(...)`, `create_agents()`, or `agent.remove()` |
| `TypeError: unhashable type: ...` when building an `AgentSet` | The agent class defines equality without a matching hash | Keep agents hashable. If you override `__eq__`, also provide a stable `__hash__` (or avoid overriding equality) |
| RNG results do not repeat across runs, or `Pass either rng or scenario, not both` appears | A seed is being split across both the model RNG and a `Scenario` instance | Choose one seed path only: `Model(rng=seed)` or `Model(scenario=Scenario(rng=seed, ...))` |
| `ValueError: Cannot schedule event in the past` | `at=` or `after=` resolved to a time earlier than `model.time` | Schedule into the future, or compute a new relative delay from the current clock. The same rule applies to recurring schedules whose `start` is in the past |
| `create_agents()` seems to split a tuple or array into pieces | Any sequence-like value whose length equals `n` is treated as one value per agent | Wrap shared values so their length no longer matches `n`, or move the data into a DataFrame and use `from_dataframe()` |
| `PendingDeprecationWarning` from `AgentSet.__getitem__` | Sequence-style indexing is deprecated | Convert first: `agentset.to_list()[0]`, `agentset.to_list()[1:3]`, or `agentset.to_list()[-1]` |

## Quick fixes

### `model.agents` assignment

```python
# Bad
model.agents = my_custom_agents

# Good
model.custom_agents = my_custom_agents
```

### Unhashable agents

```python
class MyAgent(mesa.Agent):
    __hash__ = object.__hash__
```

### Sequence broadcasting in `create_agents()`

```python
# If every agent should get the same coordinate pair, do not pass a length-n tuple.
coords = [(10, 20)] * n
MyAgent.create_agents(model, n, coords)
```

### Past-time scheduling

```python
# Schedule from the current time, not from a stale absolute value.
model.schedule_event(callback, after=1.0)
```

## What to check first

1. `model.time` before scheduling.
2. Whether the callback is a bound method or named function.
3. Whether your agent class remains hashable.
4. Whether you are using `to_list()` instead of direct indexing.
5. Whether agent counts changed through `remove()` rather than direct registry edits.
