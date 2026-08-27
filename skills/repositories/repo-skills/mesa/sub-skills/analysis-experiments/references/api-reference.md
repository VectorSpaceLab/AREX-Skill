# API Reference

This reference covers Mesa's analysis and experimental experiment APIs. Anything imported from `mesa.experimental` is explicitly experimental: APIs may change between Mesa releases and should be isolated behind small helpers when used in long-lived projects.

## Standard `DataCollector`

```python
from mesa.datacollection import DataCollector

DataCollector(
    model_reporters=None,
    agent_reporters=None,
    agenttype_reporters=None,
    tables=None,
)
```

### Reporter families

- `model_reporters`: `{name: reporter}`; one value per call to `collect(model)`.
- `agent_reporters`: `{name: reporter}`; one row per live agent per collection step.
- `agenttype_reporters`: `{AgentSubclass: {name: reporter}}`; one row per agent of that type per collection step.
- `tables`: `{table_name: [column, ...]}`; append rows manually with `add_table_row()`.

### Reporter forms and call semantics

Model reporter forms:

| Form | Example | How it is called |
| --- | --- | --- |
| model attribute name | `"gini"` | `getattr(model, "gini")` |
| lambda | `lambda m: len(m.agents)` | `reporter(model)` |
| `functools.partial` | `partial(total, scale=2)` | `reporter(model)` |
| bound no-arg method | `self.compute_gini` | `reporter()` |
| function with params | `[some_func, [p1, p2]]` | `some_func(p1, p2)` |

Agent reporter forms:

| Form | Example | How it is called |
| --- | --- | --- |
| agent attribute name | `"wealth"` | `getattr(agent, "wealth")` through a generated accessor |
| callable or unbound method | `MyAgent.double_wealth` | `reporter(agent)` |
| lambda | `lambda a: a.wealth` | `reporter(agent)` |
| partial | `partial(agent_metric, scale=2)` | `reporter(agent)` |
| function with params | `[agent_metric, [p1, p2]]` | `agent_metric(agent, p1, p2)` |

Agent-type reporter forms mirror agent reporters, but are nested under an agent class key.

Important details:

- Model reporters are validated on first `collect(model)`.
- A model reporter that is callable but not a lambda or `partial` is treated as a no-argument callable; use a lambda, partial, or list-form reporter when the function needs the model as an argument.
- List reporters must be exactly `[callable, list_or_tuple_of_params]`.
- Agent string reporters raise an informative `AttributeError` when an agent is missing the attribute.
- Agent values that are not simple immutable scalars are deep-copied before storage.
- Avoid lambdas and local closures if the model must be pickled for process-based scenario execution.

### Collection and DataFrames

```python
dc.collect(model)
model_df = dc.get_model_vars_dataframe()
agent_df = dc.get_agent_vars_dataframe()
agenttype_df = dc.get_agenttype_vars_dataframe(MyAgent)
table_df = dc.get_table_dataframe("events")
```

Return shapes:

- `get_model_vars_dataframe()` returns one row per collection and one column per model reporter.
- `get_agent_vars_dataframe()` returns a DataFrame indexed by `Step` and `AgentID` with reporter columns.
- `get_agenttype_vars_dataframe(agent_type)` returns the same indexed shape for the requested agent type.
- `get_table_dataframe(table_name)` returns columns declared in `tables`.

Warnings and exceptions:

- Empty model or agent reporter DataFrame calls warn and return an empty DataFrame.
- Missing agent-type reporter definitions warn and return an empty DataFrame.
- Missing tables raise `TableMissingException`.
- Missing columns in `add_table_row()` raise `ValueError` unless `ignore_missing=True`.
- Non-Agent keys in `agenttype_reporters` raise `ValueError` during collection.

### Tables

```python
dc = DataCollector(tables={"events": ["step", "kind", "value"]})
dc.add_table_row("events", {"step": model.time, "kind": "birth", "value": 1})
dc.add_table_row("events", {"step": model.time}, ignore_missing=True)
```

`ignore_missing=True` fills absent declared columns with `None`. It does not allow undeclared table names.

## Experimental data collection

```python
from mesa.experimental.data_collection import (
    AgentDataSet,
    BaseDataRecorder,
    DataRecorder,
    DataRegistry,
    DataSet,
    DatasetConfig,
    JSONDataRecorder,
    ModelDataSet,
    NumpyAgentDataSet,
    ParquetDataRecorder,
    SQLDataRecorder,
    TableDataSet,
)
```

`mesa.Model` creates `model.data_registry = DataRegistry()` during initialization. Recorders expect that registry and subscribe to model signals for time changes and run-end snapshots.

### `DataRegistry`

```python
registry = DataRegistry()
registry.add_dataset(dataset)
registry.create_dataset(DataSetType, name, *args, fields=..., **kwargs)
registry.track_agents(agentset, name, fields=..., use_dirty_flag=False)
registry.track_model(model, name, fields=...)
registry.track_agents_numpy(agent_type, name, fields=..., n=100, dtype=np.float64)
registry.close()
```

Mapping helpers: `name in registry`, `registry[name]`, `registry.get(name)`, and iteration over datasets.

### Dataset types

- `AgentDataSet(name, agents, *, fields, use_dirty_flag=False)` returns a list of dictionaries including `unique_id` plus requested fields. With `use_dirty_flag=True`, cached data is reused until `set_dirty_flag()`.
- `ModelDataSet(name, model, fields)` returns a dictionary of model attributes/properties.
- `TableDataSet(name, fields)` accepts validated `add_row(row)` calls and returns a list of row dictionaries.
- `NumpyAgentDataSet(name, agent_type, fields, n=100, dtype=np.float64)` installs properties for the tracked fields on the agent class, stores contiguous NumPy rows, and exposes `data`, `data_copy`, `agent_ids`, and `active_agents`.

Dataset close behavior:

- Closed datasets reject later data access.
- `NumpyAgentDataSet.close()` removes installed properties from the agent class.
- `DataRegistry.close()` closes all registered datasets.

### `DatasetConfig`

```python
DatasetConfig(
    interval=1,
    start_time=0,
    end_time=None,
    window_size=None,
    enabled=True,
)
```

- `interval` must be positive.
- `start_time` must be non-negative.
- `end_time`, if present, must be greater than `start_time`.
- `window_size`, if present, must be positive.
- `enabled=False` defines but skips a dataset.
- `should_collect(current_time)` and `update_next_collection(current_time)` implement the collection schedule.

### Recorder classes

Common recorder methods:

```python
recorder.collect()
recorder.add_dataset(dataset, configuration=None)
recorder.enable_dataset(name)
recorder.disable_dataset(name)
recorder.get_table_dataframe(name)
recorder.get_all_dataframes()
recorder.clear(name=None)
recorder.summary()
```

Recorders:

- `DataRecorder(model, config=None)`: in-memory default. Converts NumPy, agent-list, model-dict, and custom snapshots into DataFrames; supports sliding windows and memory summaries.
- `JSONDataRecorder(model, config=None, output_dir=".")`: JSON-like snapshot storage plus `save_to_json()`. Uses `NumpyJSONEncoder` for NumPy values.
- `ParquetDataRecorder(model, config=None, output_dir=".")`: buffered Parquet output. Requires a working pandas parquet engine such as `pyarrow`.
- `SQLDataRecorder(model, config=None, db_path=":memory:")`: SQLite-backed storage plus `query(sql)`.
- `BaseDataRecorder`: abstract base for custom storage backends.

Recorder timing:

- Recorders subscribe to `model.time` changes and to model `RUN_ENDED` signals.
- `run_for()` / `run_until()` trigger a final snapshot through `RUN_ENDED` even when the final time does not align with the normal interval.
- Manual `collect()` is available for explicit snapshots and testing.

## Experimental scenarios

```python
from mesa.experimental.scenarios import (
    RunConfiguration,
    Scenario,
    ScenarioAbortedException,
    ScenarioFailedException,
    ScenarioNotFoundException,
    ScenarioNotReadyException,
    rescale_samples,
    run_scenarios,
)
from mesa.experimental.scenarios.exceptions import FailureInfo, FailureOrigin
from mesa.experimental.scenarios.store import InMemoryStore, RunId, RunRecord, Status
```

### `Scenario`

```python
Scenario(*, rng=None, scenario_id=None, replication_id=-1, **kwargs)
```

- A scenario is a frozen container for experiment parameters.
- Annotated class attributes on subclasses become defaults.
- Keyword arguments override defaults for that instance.
- `rng` is normalized to a NumPy `Generator`; the `seed_sequence` and generator class are kept for reproducibility.
- `scenario_id` defaults to an auto-incrementing class-local id.
- `replication_id=-1` denotes a parent design point; spawned replications use `0..n-1`.
- `to_dict()` includes user parameters plus seed reconstruction metadata.
- `spawn_replications(n)` creates deterministic child scenarios with shared parameters and derived seeds.
- `from_dataframe(df, rng=None, replications=None)` and `from_ndarray(array, parameter_names, rng=None, replications=None)` build lists of scenarios.
- `rescale_samples(samples, ranges, inplace=False)` maps unit-interval samples to parameter ranges.

`mesa.Model` accepts either `rng=...` or `scenario=<Scenario instance>`, not both. If `scenario` is a Scenario class, `rng` is forwarded into that class.

### `RunConfiguration`

```python
RunConfiguration(
    model_class,
    until,
    model_args=None,
    model_kwargs=None,
    outcomes=None,
    data_recorder_attr_name="data_recorder",
)
```

Default methods:

- `instantiate_model(scenario)` calls `model_class(*model_args, scenario=scenario, **model_kwargs)`.
- `run_model(model)` calls `model.run_until(until)`.
- `extract_output(model)` reads `get_all_dataframes()` or named `get_table_dataframe()` values from `getattr(model, data_recorder_attr_name)`.
- `__call__(scenario)` returns a `{outcome_name: DataFrame}` mapping.

Subclass `RunConfiguration` when model construction, stop logic, or output extraction differs from the default recorder contract.

### `run_scenarios`

```python
run_scenarios(scenarios, config, *, executor=None, store=None, progress=True)
```

- Converts `scenarios` to a list, writes them to the store, and returns the store.
- Uses `InMemoryStore()` by default.
- Runs sequentially when `executor=None`.
- Uses a caller-owned executor when supplied; process-pool usage requires picklable scenarios, config, model class, and outputs.
- Optional progress uses `tqdm` if installed.

### Stores, statuses, and failure origins

- `RunId(scenario_id, replication_id)` identifies one run.
- `RunRecord` stores `scenario`, `status`, `output`, and `failure`.
- `Status`: `PENDING`, `SUCCEEDED`, `FAILED`, `ABORTED`.
- `InMemoryStore.status()` returns a DataFrame indexed by `scenario_id` and `replication_id`.
- `retrieve_output(run_id)` returns the output for succeeded runs and raises `ScenarioNotReadyException`, `ScenarioFailedException`, `ScenarioAbortedException`, or `ScenarioNotFoundException` otherwise.
- `succeeded()`, `failed()`, `pending()`, and `aborted()` return dictionaries keyed by `RunId`.

`FailureOrigin` values:

- `INSTANTIATING`: model construction failed.
- `RUNNING`: model execution failed.
- `EXTRACTING`: output extraction failed.
- `WRITING`: output persistence or transport failed.
- `ABORTED`: the executor broke and pending work was marked aborted.

## Experimental actions

```python
from mesa.experimental.actions import Action, ActionState
```

```python
Action(agent, duration=1.0, *, name=None, priority=0.0, interruptible=True)
```

State machine: `PENDING -> ACTIVE -> COMPLETED` or `PENDING/ACTIVE -> INTERRUPTED`; interrupted actions can be resumed with `start()`.

Key members:

- Properties: `name`, `progress`, `remaining_time`, `elapsed_time`, `is_resumable`.
- Lifecycle: `start()`, `interrupt()`, `cancel()`.
- Override hooks: `on_start()`, `on_resume()`, `on_complete()`, `on_interrupt(progress)`.

Agent helpers from `mesa.Agent`:

- `agent.start_action(action)` starts an action owned by that agent.
- `agent.interrupt_for(new_action)` interrupts the current action, then starts the new one; returns `False` if the current action is non-interruptible.
- `agent.cancel_action()` cancels the current action and fires `on_interrupt()` even for non-interruptible actions.
- `agent.current_action` and `agent.is_busy` expose status.

`duration` and `priority` can be callables resolved at first start. The built-in helper does not automatically compare priorities; your model logic decides when to call `interrupt_for()`.

## Experimental continuous states

```python
from mesa.experimental.states import ContinuousState, Threshold

ContinuousState(fallback_value=0.0, rate=0.0)
Threshold(state, limit, callback, direction="crossing")
```

- `ContinuousState` is a descriptor for time-aware values, using `model.time` to extrapolate from a stored baseline.
- `rate` may be a constant or a callable `f(instance) -> float`.
- Callable rates are dependency-tracked through `mesa_signals`; agents using them should inherit `HasEmitters` and initialize observable inputs.
- Chained continuous states can produce quadratic extrapolation by tracking rate-of-rate.
- `get_rate(instance)` returns the current cached/evaluated rate.
- `Threshold` schedules a callback when a state crosses a fixed limit or an `Observable` limit.
- `direction` is `"rising"`, `"falling"`, or `"crossing"`.
- Descriptor names reserve shadow attributes such as `<state>_rate` and threshold internals; avoid name collisions.

## Experimental signals

```python
from mesa.experimental.mesa_signals import (
    ALL,
    HasEmitters,
    ListSignals,
    Message,
    ModelSignals,
    Observable,
    ObservableList,
    ObservableSignals,
    SignalType,
    aggregate,
    computed_property,
    emit,
)
```

Core APIs:

- `Observable(fallback_value=None)`: descriptor that emits `ObservableSignals.CHANGED` when its value changes.
- `ObservableList()`: list descriptor emitting `ListSignals.SET`, `INSERTED`, `APPENDED`, `REMOVED`, and `REPLACED`.
- `computed_property`: derived property with automatic dependency tracking.
- `HasEmitters.observe(name_or_ALL, signal_type_or_ALL, handler)` and `unobserve(...)` manage instance subscriptions.
- `HasEmitters.observe_class(...)`, `unobserve_class(...)`, `clear_all_class_subscriptions(...)` manage class-level subscriptions.
- `clear_all_subscriptions(name_or_ALL)` removes instance subscriptions.
- `notify(observable, signal_type, **kwargs)` emits a signal.
- `peek(name, default=None)` reads without registering a computed dependency.
- `batch()` buffers and aggregates signals on context exit.
- `suppress()` drops signals in the context.
- `emit(observable_name, signal_to_emit, when="after")` wraps methods so they emit before or after execution.
- `aggregate` is a `singledispatch` hook for custom batch aggregation.

Signal payloads are `Message(name, owner, signal_type, additional_kwargs)`.

## Experimental meta agents

Only `MetaAgent` is exported by `mesa.experimental.meta_agents`; helper functions live in the module below:

```python
from mesa.experimental.meta_agents import MetaAgent
from mesa.experimental.meta_agents.meta_agent import (
    create_meta_agent,
    evaluate_combination,
    find_combinations,
)
```

```python
find_combinations(model, group, size=(2, 5), evaluation_func=None, filter_func=None)
evaluate_combination(candidate_group, model, evaluation_func)
create_meta_agent(
    model,
    new_agent_class,
    agents,
    mesa_agent_type,
    meta_attributes=None,
    meta_methods=None,
    assume_constituting_agent_methods=False,
    assume_constituting_agent_attributes=False,
)
```

`MetaAgent` behavior:

- Inherits from `Agent` and contains an `AgentSet` of constituting agents.
- Exposes `agents`, `constituting_agents_by_type`, `constituting_agent_types`, and `get_constituting_agent_instance(agent_type)`.
- Supports `add_constituting_agents()` and `remove_constituting_agents()`.
- Adds `meta_agents` membership sets to constituting agents; `meta_agent` is kept as a deterministic backward-compatible single reference.
- `remove()` cleans up constituent references before deregistering the meta-agent.

`create_meta_agent()` either adds to an existing same-class meta-agent found through constituents, instantiates an existing meta-agent class, or dynamically creates a new class inheriting from `MetaAgent` plus the requested Mesa agent type(s).

## Routing reminder

Use this sub-skill until the output is a DataFrame, status table, or structured analysis artifact. Switch to [visualization](../../visualization/SKILL.md) for plotting/dashboard work and to [model-core](../../model-core/SKILL.md) for core model mechanics.
