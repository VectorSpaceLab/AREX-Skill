# Flow Troubleshooting

Use this guide to diagnose common CrewAI Flow and event-bus problems. Start with static graph inspection before running any flow that may call LLMs, tools, credentials, network services, or human prompts.

## Quick Triage

1. From this sub-skill directory, run the bundled static helper against a safe importable module/class:

   ```bash
   python scripts/validate_flow_graph.py path/to/my_flow.py:MyFlow
   ```

2. Plot the flow if importing the module is safe:

   ```python
   MyFlow().plot("my_flow_plot")
   ```

3. Check that every `@router` label has a matching `@listen("label")` unless the label intentionally ends execution.
4. Check that every listener target is spelled exactly like the method name or router label.
5. Check that state mutations match dict vs Pydantic access style.
6. If resuming, decide whether the flow uses `@persist`, checkpointing, or async human feedback pending state; do not mix incompatible recovery paths.

## Router Emits a Label No Listener Consumes

Symptoms:

- A branch silently stops after a router.
- Plot shows a router outcome that points nowhere.
- Static validation reports a router label with no listener.

Common causes:

- Router returns `"approved"` but the listener uses `@listen("approve")`.
- Router changed label casing during refactor.
- `@human_feedback(emit=[...])` lists an outcome that has no listener.
- `emit=[...]` declares labels that are not actually returned, or returns labels not declared.

Fix pattern:

```python
@router(check, emit=["approved", "needs_revision"])
def decide(self):
    return "approved" if self.state.approved else "needs_revision"

@listen("approved")
def publish(self): ...

@listen("needs_revision")
def revise(self): ...
```

Use `Literal["approved", "needs_revision"]` return annotations as an additional static signal.

## Listener Method Name Typo

Symptoms:

- A listener never runs.
- Static validation reports a trigger with no known method or router label.
- Plot misses an expected edge.

Common cause:

```python
@listen("generte_outline")  # typo
```

Fixes:

- Use method references when possible: `@listen(generate_outline)`.
- If listening to a router label, centralize labels as constants in the module.
- Re-run static validation after renaming methods.

## Multiple Starts Surprise

Symptoms:

- Two initialization methods run when only one was expected.
- State values are overwritten before the first listener runs.
- Event logs show multiple start methods before downstream methods.

Cause:

```python
@start()
def load_a(self): ...

@start()
def load_b(self): ...
```

This is valid; all unconditional starts fire. If `load_b` depends on `load_a`, make it a listener or conditional start:

```python
@start()
def load_a(self): ...

@listen(load_a)
def load_b(self): ...
```

For independent starts that must both finish before a downstream step, use `@listen(and_(load_a, load_b))`.

## State Mutation Type Mismatch

Symptoms:

- `TypeError: 'StateModel' object is not subscriptable`.
- `AttributeError: 'dict' object has no attribute 'field'`.
- Pydantic validation errors during initialization or persistence reload.

Fix by matching state style:

```python
# Dict state
self.state["draft"] = "..."

# Pydantic state
self.state.draft = "..."
```

For structured state, define all fields that methods mutate:

```python
class DraftState(BaseModel):
    draft: str = ""
    revision_count: int = 0
```

Avoid shared mutable defaults. Prefer `Field(default_factory=list)` or `Field(default_factory=dict)` for collections.

## Plotting Dependency or Path Errors

Symptoms:

- Plot file is not created.
- Plot path has unexpected suffix or location.
- Static graph omits router labels.

Checks:

- Call `flow.plot("name")`; CrewAI writes an HTML file and adds `.html` when needed.
- Ensure the current working directory or target directory is writable.
- Add `emit=[...]` to routers or `Literal[...]` return types so possible labels are visible statically.
- Confirm importing the flow module does not require unavailable credentials or side effects.

If CLI plotting is part of a scaffolded project, route command syntax to [cli-and-projects](../../cli-and-projects/SKILL.md).

## Persistence and Checkpoint Duplicate Calls

Symptoms:

- A method appears to run twice after resume.
- A human feedback review loop repeats an already approved step.
- `ValueError` appears when both checkpoint and persisted state restore are passed.

Separate the mechanisms:

| Mechanism | Resume call | Use for |
| --- | --- | --- |
| `@persist` same lineage | `kickoff(inputs={"id": state_id})` | Continue application state history. |
| `@persist` fork | `kickoff(restore_from_state_id=state_id)` | Start a new state id from a prior snapshot. |
| checkpointing | `kickoff(from_checkpoint=CheckpointConfig(...))` | Resume execution and skip completed methods/tasks. |
| async human feedback | `Flow.from_pending(flow_id).resume(feedback)` | Resume a paused HITL method. |

Do not combine `from_checkpoint` with `restore_from_state_id`.

For conversational flows, prefer persisting at one terminal step rather than class-level `@persist` on every method; otherwise restore can pick a mid-turn snapshot before the assistant handler appended its response.

## Human Feedback Loop Does Not Stop

Symptoms:

- Review method keeps repeating.
- Pressing Enter causes another revision unexpectedly.
- Approval listener never fires.

Checks:

- `default_outcome` must be intentional and one of `emit`.
- Revision loops should be on a listener that listens to both the upstream trigger and the revision outcome:

  ```python
  @human_feedback(emit=["approved", "needs_revision"], default_outcome="needs_revision", llm="...")
  @listen(or_(generate, "needs_revision"))
  def review(self): ...
  ```

- A `@start()` method runs once; do not put the self-loop on the start method.
- Ensure `max_method_calls` is high enough for intended loops but low enough to catch accidental infinite cycles.
- If `emit` is used, configure an LLM that can classify the feedback. Without `emit`, listeners receive `HumanFeedbackResult` from the decorated method instead of route labels.

## Human Feedback Pauses Unexpectedly

Symptoms:

- `kickoff()` returns a pending object instead of a final result.
- Events show `method_execution_paused` or `flow_paused`.

Cause:

A custom async feedback provider raised `HumanFeedbackPending`. This is expected for webhook, Slack, or UI review flows.

Fix:

- Return the pending callback information to the caller.
- Resume later with `Flow.from_pending(flow_id).resume(feedback)` or `await resume_async(feedback)`.
- Use the sync resume method outside an event loop and async resume inside async web frameworks.

## Event Listener Not Firing

Symptoms:

- Custom event listener class exists but no handler output appears.
- `crewai_event_bus.on(...)` handler works in a test but not in the app.

Checks:

- Instantiate the listener before executing the flow.
- Import the module that creates the listener instance.
- Keep the listener instance in module scope.
- Use the exact event class, such as `MethodExecutionStartedEvent` rather than a similarly named string.
- For temporary debug handlers, wrap execution in `crewai_event_bus.scoped_handlers()`.

## Event Order Looks Wrong

Symptoms:

- Captured events appear out of sequence.
- Parallel listeners make ordering nondeterministic.

CrewAI can dispatch handlers asynchronously. Sort captured events by `timestamp` or inspect event ids. For causality, use `triggered_by_event_id`: listener starts point to the upstream method finish event that triggered them.

## Flow Runs Live LLMs During Validation

Symptoms:

- A diagnostic run prompts for API keys or calls models.
- Importing a module starts work before validation.

Safe practice:

- Do not call `kickoff()` for graph validation.
- Use `validate_flow_graph.py` first; it imports only when explicitly given a target and does not call `kickoff()`.
- Keep module top-level code guarded by `if __name__ == "__main__":`.
- Move live crews, tools, and LLM calls inside flow methods rather than module import time.

## `and_` Join Never Runs

Symptoms:

- A convergence method never executes.
- Each upstream path works independently.

Causes:

- One required method is on a mutually exclusive route branch.
- One upstream method name was misspelled.
- A router label is listened to where a method completion was intended, or vice versa.

Fix:

- Join only paths that can all happen in the same run.
- Use separate joins for mutually exclusive branches.
- Plot the graph and inspect condition trees.

## Conversational Flow Uses Wrong API

Symptoms:

- `kickoff(user_message=..., session_id=...)` fails.
- The second chat turn does not include the first assistant response.
- Trace sessions never finalize.

Fix:

- Use `flow.handle_turn(message, session_id=session_id)` for each chat line.
- Append assistant replies with `append_assistant_message(...)` when writing custom handlers.
- Call `finalize_session_traces()` when the session ends if trace finalization is deferred.
- Do not use `@human_feedback` for ordinary follow-up chat messages.

## Static Validator Reports Import Error

Possible causes:

- Target module has missing dependencies.
- Target module runs side effects at import time.
- Target class is not a `Flow` subclass.

Fixes:

- Pass a file path plus class name: `module.py:ClassName`.
- Keep top-level code side-effect-free.
- If imports require optional dependencies, install only the safe package extras needed for inspection or validate a reduced module containing the Flow class.

## Hard-Case Debug Recipes

### Router Label Not Consumed

1. Run `python scripts/validate_flow_graph.py module.py:FlowClass --json`.
2. Check `warnings.router_labels_without_listeners`.
3. Confirm labels from `emit`, `Literal[...]`, and human feedback outcomes.
4. Add missing listeners or document terminal labels in the flow code for reviewers.
5. Plot the flow and inspect the branch visually before execution.

### Typed State Resume After Human Feedback

1. Use a Pydantic state model with explicit fields for draft, revision count, status, and audit notes.
2. Put the approval loop on a listener with `or_(upstream, "needs_revision")`.
3. Use `@persist` on a terminal post-review method or a custom async provider's pending/resume flow, not both checkpoint restore and persisted-state fork in the same kickoff.
4. Store feedback summaries in `human_feedback_history` or state audit fields.
5. Set `max_method_calls` to catch runaway revision loops.

## Source Artifact Note

Flow CLI templates and project commands were intentionally excluded from this troubleshooting reference except as routing notes. Future agents should use [cli-and-projects](../../cli-and-projects/SKILL.md) for CLI command syntax and scaffold structure, and [observability-and-hooks](../../observability-and-hooks/SKILL.md) for tracing/export provider configuration.
