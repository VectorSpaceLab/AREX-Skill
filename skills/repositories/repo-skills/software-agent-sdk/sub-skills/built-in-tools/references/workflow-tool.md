# Workflow Tool

## Script contract

A workflow script must define:

```python
async def main(wf):
    ...
```

The `wf` object exposes:

- `await wf.run_agent(prompt, subagent_type="general-purpose", description=None)`
- `await wf.map_agents(items, prompt, subagent_type="general-purpose", max_concurrency=None, description=None)`
- `await wf.reduce_agent(items, prompt, subagent_type="general-purpose", description=None)`
- `await wf.pipeline(items, *stages)`
- `wf.flatten(values)`

## Safety and behavior

- Scripts should coordinate sub-agents only through `wf` methods.
- The workflow validator rejects missing `async def main(wf)` and unsafe direct file or shell access.
- `map_agents()` may raise an `ExceptionGroup` when any sub-agent fails.
- Keep reducer prompts concise because large intermediate results may be truncated.

## Minimal example

```python
async def main(wf):
    plans = await wf.map_agents(["a", "b"], prompt="Review {item}")
    return await wf.reduce_agent(plans, prompt="Summarize the review")
```
