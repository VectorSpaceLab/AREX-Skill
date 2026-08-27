# API Reference

## Verified Mesa 4 baseline

- Mesa version: **4.0.0a0**
- Python: **3.12+**
- `Model(*args, rng=None, scenario=Scenario, **kwargs)`
- `Agent(model, *args, **kwargs)`
- `Agent.create_agents(model, n, *args, **kwargs)`
- `Agent.from_dataframe(model, df, **kwargs)`
- `Schedule(interval=1.0, start=None, end=None, count=None)`

## Core object map

```text
Model
├─ owns model.agents                 -> strong-ref AgentSet-like registry
├─ owns model.agents_by_type         -> type -> AgentSet-like registry
├─ owns model.agent_types            -> list of registered agent classes
├─ owns model.time                   -> simulation clock
├─ schedules user step               -> every 1.0 time units by default
├─ schedules events                  -> Event / EventGenerator / EventList
└─ exposes rng / random / scenario   -> reproducible randomness

Agent
├─ registers itself in Model.__init__
├─ gets unique_id from its model
├─ exposes model / random / rng / scenario
└─ deregisters with agent.remove()

AgentSet
├─ ordered set semantics over agents
├─ supports select / shuffle / sort / do / shuffle_do / map / agg / get / set / groupby
└─ sequence indexing is deprecated; use to_list()

GroupBy
├─ wraps named groups
├─ supports get_group / map / do / count / agg / iteration
└─ group values may be AgentSet-like or plain lists

Event scheduling
├─ Event: one-off callback
├─ EventGenerator: recurring callback runner
├─ EventList: ordered event queue
└─ Priority: HIGH / DEFAULT / LOW ordering
```

## Signatures to rely on

### `mesa.Model`

- `__init__(*args, rng=None, scenario=Scenario, **kwargs)`
- `run_model()` loops while `self.running` is true and calls `step()`
- `run_for(duration)` advances by a relative duration
- `run_until(end_time)` advances to an absolute time
- `schedule_event(function, *, at=None, after=None, priority=Priority.DEFAULT)` returns `Event`
- `schedule_recurring(function, schedule, priority=Priority.DEFAULT)` returns `EventGenerator`
- `remove_all_agents()` removes every registered agent

### `mesa.Agent`

- `__init__(model, *args, **kwargs)` registers the agent immediately
- `remove()` deregisters the agent and cancels any active action
- `step()` and `advance()` are extension points
- `random` is the stdlib RNG from the model
- `rng` is the NumPy generator from the model
- `scenario` is the model's scenario object

### `Agent.create_agents`

- Positional and keyword values that look like sequences and have length `n` are split elementwise across the created agents.
- Non-sequence values, or sequences whose length does not match `n`, are repeated for every agent.
- Returns an `AgentSet` view for the new agents.

### `Agent.from_dataframe`

- Each row becomes one agent.
- DataFrame columns map to constructor kwargs.
- Extra kwargs must be scalar-like; sequence kwargs are rejected.

### `mesa.time`

- `Event(time, function, priority=Priority.DEFAULT, function_args=None, function_kwargs=None)`
- `Schedule(interval=1.0, start=None, end=None, count=None)`
- `EventGenerator(model, function, schedule, priority=Priority.DEFAULT)`
- `EventList()` with `add_event`, `pop_event`, `peek_ahead`, `remove`, `compact`, `clear`
- `Priority.HIGH == 1`, `Priority.DEFAULT == 5`, `Priority.LOW == 10`

### Key time-object methods

- `Event.execute()` runs the callback if the event is still live.
- `Event.cancel()` marks the event canceled and clears its callback state.
- `EventGenerator.start()` activates recurring scheduling.
- `EventGenerator.stop()` cancels future firings.
- `EventGenerator.pause()` keeps the generator active but suspends the next event.
- `EventGenerator.resume()` restarts a paused generator from the current time.
- `EventList.add_event()` inserts a new event into the priority queue.
- `EventList.pop_event()` removes the next live event in time/priority order.
- `EventList.peek_ahead()` inspects upcoming live events without removing them.
- `EventList.remove()` lazily cancels an event.
- `EventList.compact()` drops canceled events from the heap.
- `EventList.clear()` empties the queue.

## Object relationships that matter

- `Agent.__init__` calls `model.register_agent(self)`; creation is enough to register an agent.
- `register_agent()` assigns `unique_id` and stores the agent in both the global registry and the type registry.
- `agent.remove()` calls `model.deregister_agent(self)`; use this instead of mutating registries directly.
- `model.agents` is the live registry. Treat it as read-mostly.
- `model.agents_by_type[SomeAgent]` gives the live registry for that class.
- `schedule_event()` and `schedule_recurring()` store callbacks in the model's event queue; `run_for()` / `run_until()` process that queue while advancing time.

## AgentSet and GroupBy operations

### AgentSet

Typical calls:

- `select(filter_func=None, at_most=inf, inplace=False, agent_type=None)`
- `shuffle(inplace=False)`
- `sort(key, ascending=False, inplace=False)`
- `do(method, *args, **kwargs)`
- `shuffle_do(method, *args, **kwargs)`
- `map(method, *args, **kwargs)`
- `agg(attribute, func)`
- `get(attr_names, handle_missing="error", default_value=None)`
- `set(attr_name, value)`
- `groupby(by, result_type="agentset")`
- `to_list()`

Use `to_list()` when you need indexing or slicing.

### GroupBy

- `get_group(name, default=...)`
- `map(method, *args, **kwargs)`
- `do(method, *args, **kwargs)`
- `count()`
- `agg(attr_name, func)`
- Iteration yields `(group_name, group)` pairs.

## Event timing and ordering

- One-off events run at a specific `time`.
- Recurring generators compute the next firing time from the schedule interval.
- Events at the same time are ordered by `Priority` first, then by creation order.
- `Schedule.interval` may be a callable `interval(model)`; it must return a positive value.
- `Schedule.start`, `Schedule.end`, and `Schedule.count` are all optional bounds.

## Validation signals

Use these checks when you need to prove the core API is working:

- `len(model.agents)` matches the number of live agents.
- `agent.unique_id` is assigned only after `super().__init__(model)` completes.
- `model.agent_types` and `model.agents_by_type` update automatically when agents are created.
- `model.time` advances through `step()`, `run_for()`, `run_until()`, and scheduled events.
- `Priority.HIGH` callbacks run before `DEFAULT` and `LOW` callbacks at the same timestamp.
- `EventGenerator.stop()` prevents future firings; `Event.cancel()` removes one-off events.

## Gotchas

- `Agent.__init__` auto-registers the agent. Do not append directly to `model.agents`.
- `model.agents` cannot be reassigned; its setter raises `AttributeError`.
- Agents must be hashable to live in an AgentSet.
- `AgentSet.__getitem__` is deprecated; use `agentset.to_list()[index]` instead.
- Do not pass both `rng` and a `Scenario` instance to `Model`.
- `schedule_event()` requires exactly one of `at` or `after`.
- `schedule_event()` and `schedule_recurring()` reject past times.
- Use named functions or bound methods for scheduled callbacks; weak references mean ephemeral callables are unsafe.
- `create_agents()` treats length-matching sequences as per-agent values.
- `from_dataframe()` rejects sequence kwargs; move varying values into the DataFrame.

## Where to go next

- Use [workflows](workflows.md) for concrete recipes.
- Use [troubleshooting](troubleshooting.md) for fixes.
- Use [the smoke script](../scripts/mesa_model_smoke.py) for a runnable core check.
