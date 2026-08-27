# Troubleshooting

All `mesa.experimental` APIs are unstable by design. When a behavior matters to a project, pin a Mesa version and add a small smoke or regression test around the exact import path and output shape.

## `DataCollector.collect()` raises during reporter validation

### Symptoms

- `RuntimeError` mentioning a model reporter name.
- `AttributeError` for a missing model or agent attribute.
- `ValueError` mentioning `[function, [param1, param2]]`.

### Common causes

- A model string reporter points at a missing model attribute.
- A model callable reporter is not callable with the semantics Mesa expects.
- A model callable was passed as an unbound method that needs `model`; non-lambda/non-partial model callables are called with no arguments.
- A list reporter is malformed; the second item must be a list or tuple of parameters.
- An agent string reporter references an attribute missing on at least one collected agent.

### Fixes

- For model attributes, use `{"name": "model_attr"}` only when every collected model has that attribute.
- For model methods, prefer bound no-argument methods such as `self.compute_metric`.
- For functions that need the model, use `lambda m: func(m)` or `functools.partial(func, ...)` if pickling is not needed; use a top-level function plus a thin bound method when pickling is needed.
- For agent reporters, use strings for simple attributes and callables that accept one agent.
- Recreate the `DataCollector` instead of mutating reporter internals after first validation.

## Agent-type reporters are empty or fail

### Symptoms

- `get_agenttype_vars_dataframe(SomeType)` warns and returns an empty DataFrame.
- Collection raises a `ValueError` that the type is not recognized as an Agent type.

### Common causes

- No reporters were registered for that exact type.
- The type key is not a subclass of `mesa.Agent`.
- The model has no instances of that type or subclass at collection time.

### Fixes

- Define `agenttype_reporters={MyAgent: {"metric": "attr"}}` when building the collector.
- Use real `Agent` subclasses as keys.
- Confirm agents have been created and registered before `collect()`.
- If collecting a superclass, confirm actual agents are instances of that superclass.

## DataFrame shape surprises

### Symptoms

- Agent DataFrames have more rows than expected.
- `Step` / `AgentID` appear as an index instead of regular columns.
- Model DataFrames have one extra row.

### Common causes

- `collect()` was called at initialization plus every step.
- Agent-level output is one row per live agent per collection time.
- `get_agent_vars_dataframe()` and `get_agenttype_vars_dataframe()` use a MultiIndex.

### Fixes

- Count explicit `collect()` calls and multiply by live agent counts.
- Use `.reset_index()` before merging or serializing agent outputs.
- Keep the initial snapshot only if your analysis needs baseline time zero.

## Table errors

### Symptoms

- `TableMissingException` from `add_table_row()` or `get_table_dataframe()`.
- `ValueError: Could not insert row with missing column ...`.

### Common causes

- The table was not declared in `DataCollector(..., tables={...})`.
- The row omits a declared column.
- The row includes values that are not DataFrame/JSON friendly.

### Fixes

- Declare every table up front.
- Pass all columns for ordinary rows.
- Use `ignore_missing=True` only when `None` is a meaningful placeholder.
- Normalize complex objects before appending rows.

## Recorder initialization fails

### Symptoms

- `AttributeError: Model must have a DataRegistry (model.data_registry)`.
- `KeyError` for a dataset name during recorder construction.
- No rows appear after stepping.

### Common causes

- A custom model removed or failed to initialize `model.data_registry`.
- `config` references a dataset that has not been registered.
- The recorder was created before datasets and the later dataset was not added with `record()` or `add_dataset()`.
- `DatasetConfig(enabled=False)`, future `start_time`, or `end_time` prevents collection.

### Fixes

- Always call `super().__init__()` in `Model.__init__()`.
- Register datasets before constructing a recorder with `config={...}`.
- For late datasets, call `dataset.record(recorder, configuration=...)` or `recorder.add_dataset(dataset, configuration=...)`.
- Inspect `recorder.summary()` and `recorder.configs[name]`.
- Call `recorder.collect()` once manually when debugging.

## Experimental recorder backend issues

### Symptoms

- Parquet read/write fails.
- JSON output is missing or contains non-serializable objects.
- SQLite operations fail or return empty tables.

### Common causes

- `ParquetDataRecorder` needs a pandas parquet engine such as `pyarrow`.
- JSON snapshots include custom objects that `NumpyJSONEncoder` does not convert.
- SQLite path is not writable, table was never created because no data was collected, or the connection was closed.

### Fixes

- Fall back to `DataRecorder` for smoke tests.
- Treat Parquet as optional and probe availability before choosing it.
- Convert custom objects to primitive dictionaries before recording.
- Use `SQLDataRecorder(db_path=":memory:")` to isolate database issues.
- Check `get_table_dataframe(name)` after a manual `collect()`.

## Scenario/model RNG conflict

### Symptom

`Model(...)` raises `ValueError: Pass either rng or scenario, not both.`

### Fixes

- Pass `Model(rng=42)` when Mesa should construct the default scenario.
- Pass `Model(scenario=my_scenario)` when you already built a scenario.
- Pass `Model(rng=42, scenario=MyScenarioClass)` only when `scenario` is a class, not an instance.
- Use `Scenario.spawn_replications(n)` for deterministic replications instead of mutating a frozen scenario.

## Scenario sweep records failures

### Symptoms

- `store.failed()` is non-empty.
- `store.retrieve_output(run_id)` raises `ScenarioFailedException`.
- Failure records contain `origin`, `exception_type`, and `message`.

### How to debug by origin

- `instantiating`: call `config.instantiate_model(scenario)` directly.
- `running`: instantiate once and call `config.run_model(model)` directly with a tiny horizon.
- `extracting`: call `config.extract_output(model)` after a known-good run and verify recorder/outcome names.
- `writing`: inspect returned DataFrames, store writer, filesystem/database permissions, and picklability.
- `aborted`: debug executor/worker crash first; aborted pending runs are often secondary.

## Process-pool or pickling failures

### Symptoms

- Process executor runs fail while sequential runs succeed.
- Failure origin is `writing`, or pending runs become `aborted`.
- Errors mention pickling, local classes, lambdas, or broken process pools.

### Fixes

- Define `Scenario`, `Model`, and `RunConfiguration` classes at module top level.
- Avoid lambdas and nested functions in reporters, scenarios, and config objects.
- Keep scenario attributes primitive or picklable.
- Return pandas DataFrames or simple serializable structures from `extract_output()`.
- Re-run sequentially with `executor=None` to isolate model logic from transport issues.

## Action lifecycle errors

### Symptoms

- `start_action()` raises because the agent is already busy.
- `interrupt_for()` returns `False`.
- An action cannot be restarted.
- Cleanup code in `on_interrupt()` did not run when an agent was removed.

### Common causes

- Only one active action is allowed per agent.
- The action belongs to a different agent.
- The current action is non-interruptible.
- The action is already `ACTIVE` or `COMPLETED`.
- `Agent.remove()` silently cancels active action events without firing `on_interrupt()`.

### Fixes

- Check `agent.is_busy` and `agent.current_action`.
- Use `agent.interrupt_for(new_action)` for preemption.
- Use `agent.cancel_action()` when cleanup must run regardless of `interruptible`.
- Resume only actions in `INTERRUPTED` state with `action.is_resumable`.
- Override `remove()` and call `cancel_action()` before `super().remove()` when action cleanup matters.

## Signals do not fire, fire late, or fire too often

### Symptoms

- Handlers are not called.
- `computed_property` values appear stale during a block.
- List mutations collapse into one signal.

### Common causes

- The class does not inherit `HasEmitters`.
- The observable name or signal enum does not match the descriptor.
- The handler was garbage-collected because subscriptions store weak references.
- `batch()` deferred and aggregated signals.
- `suppress()` dropped signals.

### Fixes

- Use `class MyAgent(Agent, HasEmitters): ...` for agent observables.
- Keep a strong reference to handlers when they are not bound methods.
- Use `ObservableSignals.CHANGED`, `ListSignals.*`, or `ModelSignals.*` from the correct enum.
- Use `batch()` only when aggregation is desired.
- Do not use `suppress()` around changes that should invalidate computed properties.
- Use `peek()` when a read should not register as a dependency.

## Continuous state or threshold issues

### Symptoms

- A threshold never fires or fires repeatedly.
- A continuous value jumps unexpectedly.
- Class creation raises a namespace collision error.
- A callable rate raises during initialization.

### Common causes

- The agent does not inherit `HasEmitters` but uses callable-rate states or thresholds.
- A state name collides with generated shadow names such as `<state>_rate`.
- The rate callable reads an observable before it has been initialized.
- The threshold direction rejects the crossing (`rising`, `falling`, `crossing`).
- The callback changes rate/limit and immediately reschedules another crossing.

### Fixes

- Initialize observable inputs before first meaningful state read.
- Keep descriptor names distinct from generated shadow names.
- Use constant rates first, then add callable rates once the simple trajectory works.
- Inspect `type(agent).state_descriptor.get_rate(agent)` for the current rate.
- Verify the sign of the velocity at the threshold for the chosen direction.

## Meta-agent grouping surprises

### Symptoms

- `create_meta_agent()` returns an existing meta-agent instead of a new one.
- Constituting agents keep stale or unexpected membership references.
- Inferred attributes or methods override expectations.

### Common causes

- If any constituent already belongs to a same-class meta-agent, creation extends that existing group.
- `assume_constituting_agent_methods=True` and `assume_constituting_agent_attributes=True` infer members from constituents.
- Backward-compatible `agent.meta_agent` stores only one deterministic reference, while `agent.meta_agents` stores all memberships.

### Fixes

- Use unique `new_agent_class` names when independent group classes are required.
- Prefer explicit `meta_attributes` and `meta_methods`.
- Read and write `agent.meta_agents` for multiple memberships.
- Call `meta_agent.remove()` or `remove_constituting_agents()` to clean membership references.

## Smoke scripts fail

### Symptoms

- `datacollector_smoke.py` or `scenario_smoke.py` prints `"ok": false`.

### Common causes

- Mesa is not importable in the current Python environment.
- `pandas` is missing or broken.
- Experimental scenario APIs are unavailable in the installed Mesa version.

### Fixes

- Run the script with the Python environment that has Mesa installed.
- Confirm `python -c "import mesa; print(mesa.__version__)"` works.
- Treat a missing experimental import as a version/API mismatch and narrow the workflow to stable `DataCollector` APIs.
