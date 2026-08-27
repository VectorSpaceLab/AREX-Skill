# Workflow Recipes

These recipes assume an installed Mesa package. APIs under `mesa.experimental` are experimental; keep wrappers small and add smoke tests around the exact behavior your project depends on.

## 1) Use `DataCollector` for simple in-memory analysis

Choose `DataCollector` when you need a compact model-level trend table, per-agent snapshots, agent-type-specific snapshots, or a manual event table.

```python
from mesa import Agent, Model
from mesa.datacollection import DataCollector

class Person(Agent):
    def __init__(self, model, wealth):
        super().__init__(model)
        self.wealth = wealth

    def step(self):
        self.wealth += 1

    def doubled_wealth(self):
        return self.wealth * 2

class WealthModel(Model):
    def __init__(self, n=3):
        super().__init__(rng=42)
        Person.create_agents(self, n, list(range(n)))
        self.datacollector = DataCollector(
            model_reporters={
                "agent_count": self.agent_count,
                "total_wealth": self.total_wealth,
            },
            agent_reporters={
                "wealth": "wealth",
                "doubled": Person.doubled_wealth,
            },
            agenttype_reporters={
                Person: {"wealth": "wealth"},
            },
            tables={"events": ["time", "event", "total_wealth"]},
        )
        self.record("initial")

    def agent_count(self):
        return len(self.agents)

    def total_wealth(self):
        return sum(agent.wealth for agent in self.agents)

    def record(self, event):
        self.datacollector.collect(self)
        self.datacollector.add_table_row(
            "events",
            {"time": self.time, "event": event, "total_wealth": self.total_wealth()},
        )

    def step(self):
        self.agents.do("step")
        self.record("step")
```

Extract outputs:

```python
model = WealthModel()
model.run_for(5)

model_df = model.datacollector.get_model_vars_dataframe()
agent_df = model.datacollector.get_agent_vars_dataframe().reset_index()
person_df = model.datacollector.get_agenttype_vars_dataframe(Person).reset_index()
events_df = model.datacollector.get_table_dataframe("events")
```

Validation checklist:

- `len(model_df)` equals the number of explicit `collect()` calls.
- `agent_df` has `Step` and `AgentID` index columns after `reset_index()`.
- Agent-type DataFrames only include rows for the requested type.
- Manual tables contain only declared columns.

## 2) Use experimental `DataRegistry` and recorders for scheduled snapshots

Choose the experimental recorder stack when you need automatic collection by simulation time, windowed retention, file-backed artifacts, or backend-specific storage.

```python
from mesa import Agent, Model
from mesa.experimental.data_collection import DataRecorder, DatasetConfig

class Worker(Agent):
    def __init__(self, model, load):
        super().__init__(model)
        self.load = load

    def step(self):
        self.load += 0.5

class RecorderModel(Model):
    @property
    def mean_load(self):
        return self.agents.agg("load", lambda values: sum(values) / len(values))

    def __init__(self):
        super().__init__(rng=42)
        Worker.create_agents(self, 4, [1.0, 2.0, 3.0, 4.0])

        self.data_registry.track_agents(self.agents, "workers", fields="load")
        self.data_registry.track_model(self, "model", fields=["time", "mean_load"])

        self.data_recorder = DataRecorder(
            self,
            config={
                "workers": DatasetConfig(interval=1, start_time=0, window_size=10),
                "model": DatasetConfig(interval=2, start_time=0),
            },
        )

    def step(self):
        self.agents.do("step")
```

Run and extract:

```python
model = RecorderModel()
model.run_for(5)
workers = model.data_recorder.get_table_dataframe("workers")
model_rows = model.data_recorder.get_table_dataframe("model")
summary = model.data_recorder.summary()
```

Recorder selection:

| Need | Recorder | Notes |
| --- | --- | --- |
| Fast local analysis | `DataRecorder` | In-memory default; best first choice |
| Portable lightweight logs | `JSONDataRecorder` | Call `save_to_json()` when ready to persist |
| Columnar analytics | `ParquetDataRecorder` | Requires a parquet engine; keep optional |
| SQL querying | `SQLDataRecorder` | Uses SQLite; `db_path=":memory:"` is safe for smoke tests |
| Custom transport/storage | subclass `BaseDataRecorder` | Implement storage, DataFrame extraction, clear, and summary |

Patterns:

- Track datasets before constructing the recorder when you want initial storage initialized from `config`.
- Use `dataset.record(recorder, configuration=...)` or `recorder.add_dataset(...)` when adding after recorder construction.
- Use `window_size` for rolling windows.
- Use `enabled=False` to keep a dataset configured but quiet.
- Rely on `run_for()` / `run_until()` to emit final snapshots through model `RUN_ENDED` when using recorder auto-collection.

## 3) Run reproducible scenario sweeps

Use scenarios when you need immutable design points, deterministic replications, status accounting, and structured failure records.

```python
import pandas as pd
from mesa.experimental.scenarios import Scenario, RunConfiguration, run_scenarios

class ExperimentScenario(Scenario):
    n_agents: int = 10
    start_load: float = 1.0

scenarios = ExperimentScenario.from_dataframe(
    pd.DataFrame(
        [
            {"n_agents": 5, "start_load": 1.0},
            {"n_agents": 8, "start_load": 2.0},
        ]
    ),
    rng=42,
    replications=3,
)

config = RunConfiguration(RecorderModel, until=20, outcomes=["model"])
store = run_scenarios(scenarios, config, progress=False)
```

Read outputs and failures:

```python
from mesa.experimental.scenarios.store import RunId

status_df = store.status()
failed = store.failed()
aborted = store.aborted()

for run_id, record in store.succeeded().items():
    model_df = store.retrieve_output(run_id)["model"]
```

When to subclass `RunConfiguration`:

```python
class SummaryRun(RunConfiguration):
    def run_model(self, model):
        # Custom stop logic is allowed.
        while model.time < self.until and model.running:
            model.step()

    def extract_output(self, model):
        # Return outcome-name -> DataFrame.
        return {"summary": model.data_recorder.get_table_dataframe("model")}
```

Parallel execution tips:

- Pass a caller-owned executor, for example a `ProcessPoolExecutor`, to `run_scenarios(..., executor=executor)`.
- Keep scenario classes, model classes, and `RunConfiguration` subclasses importable at module top level when using process pools.
- Avoid lambdas, local closures, and non-picklable objects in scenarios, recorders, and outputs.
- A failed individual run is recorded as `FAILED`; a broken process pool marks pending runs as `ABORTED`.

## 4) Interpret scenario failure origins

```python
for run_id, record in store.failed().items():
    failure = record.failure
    print(run_id, failure.origin.value, failure.exception_type, failure.message)
```

Use the origin to choose the next probe:

| Origin | Probe |
| --- | --- |
| `instantiating` | Instantiate the model directly with the failing scenario. |
| `running` | Run `config.run_model(model)` directly with a tiny `until`. |
| `extracting` | Inspect `config.extract_output(model)` and the recorder/outcome names. |
| `writing` | Check store writer, returned objects, pickling, and filesystem/database paths. |
| `aborted` | Debug the executor or worker crash before rerunning the sweep. |

## 5) Model timed work with experimental `Action`

Use actions when agent work spans simulation time and may be interrupted or resumed.

```python
from mesa import Agent, Model
from mesa.experimental.actions import Action

class Forage(Action):
    def __init__(self, sheep):
        super().__init__(sheep, duration=5.0, interruptible=True)

    def on_complete(self):
        self.agent.energy += 10

    def on_interrupt(self, progress):
        self.agent.energy += 10 * progress

class Sheep(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 0

class ActionModel(Model):
    def __init__(self):
        super().__init__(rng=42)
        self.sheep = Sheep(self)
        self.sheep.start_action(Forage(self.sheep))
```

Operational rules:

- Create the action with the agent that will own it.
- Use `agent.start_action(action)` when idle.
- Use `agent.interrupt_for(new_action)` to preempt an interruptible action.
- Use `agent.cancel_action()` when teardown should call `on_interrupt()`.
- If an agent is removed, the default cleanup cancels the scheduled event silently; explicitly call `cancel_action()` first if the callback must run.

## 6) Use experimental signals and continuous states for reactive analysis

Signals are useful when derived analysis variables must react to state changes.

```python
from mesa import Agent, Model
from mesa.experimental.mesa_signals import HasEmitters, Observable, ObservableSignals, computed_property

class ReactiveAgent(Agent, HasEmitters):
    wealth = Observable()
    tax_rate = Observable()

    def __init__(self, model, wealth, tax_rate):
        super().__init__(model)
        self.wealth = wealth
        self.tax_rate = tax_rate

    @computed_property
    def after_tax_wealth(self):
        return self.wealth * (1 - self.tax_rate)

model = Model(rng=42)
agent = ReactiveAgent(model, 100, 0.2)
agent.observe("after_tax_wealth", ObservableSignals.CHANGED, lambda msg: print(msg.name))
agent.wealth = 120
```

Batching and suppression:

```python
with agent.batch():
    agent.wealth = 130
    agent.tax_rate = 0.25

with agent.suppress():
    agent.wealth = 140  # no signal is emitted
```

Continuous state pattern:

```python
from mesa.experimental.states import ContinuousState, Threshold

class Vehicle(Agent, HasEmitters):
    speed = Observable()
    position = ContinuousState(rate=lambda a: a.speed)
    arrival = Threshold(position, limit=100.0, callback="arrive", direction="rising")

    def __init__(self, model, speed):
        super().__init__(model)
        self.speed = speed

    def arrive(self):
        self.speed = 0.0
```

Guidelines:

- Inherit `HasEmitters` for classes that define `Observable`, `computed_property`, `ObservableList`, callable-rate `ContinuousState`, or `Threshold` descriptors.
- Initialize observable backing values before relying on computed values.
- Use `peek(name, default)` inside computations when a read should not become a dependency.
- `batch()` delays signals and coalesces common observable/list changes; `suppress()` drops them.

## 7) Analyze higher-order groups with experimental meta agents

Use meta agents when a task needs to form and analyze agent groups as first-class agents.

```python
from mesa.experimental.meta_agents.meta_agent import create_meta_agent, find_combinations

pairs = find_combinations(
    model,
    model.agents,
    size=2,
    evaluation_func=lambda group: sum(agent.wealth for agent in group),
    filter_func=lambda scored: [item for item in scored if item[1] > 10],
)

for agents, score in pairs:
    coalition = create_meta_agent(
        model,
        "Coalition",
        agents,
        mesa_agent_type=None,
        meta_attributes={"score": score},
    )
```

After creation:

```python
len(coalition)
coalition.agents
coalition.constituting_agents_by_type
coalition.constituting_agent_types
coalition.get_constituting_agent_instance(SomeAgentClass)
```

Keep meta-agent logic explicit: dynamic classes and inferred attributes/methods are powerful but can hide collisions. Prefer explicit `meta_attributes` and `meta_methods` for reproducible experiments.

## 8) Suggested analysis workflow order

1. Decide whether the task needs simple collection, scheduled recording, or scenario orchestration.
2. Use `DataCollector` for quick model/agent/table DataFrames.
3. Use experimental `DataRegistry` + a recorder for periodic or file-backed snapshots.
4. Use `Scenario` + `RunConfiguration` + `run_scenarios` for design matrices and replications.
5. Add `Action`, `ContinuousState`, `Threshold`, or `mesa_signals` only when model behavior or analysis state is inherently timed/reactive.
6. Add meta agents only when groups need to be first-class agents.
7. Hand plotting or dashboards to [visualization](../../visualization/SKILL.md) after DataFrames are produced.

## Smoke checks

From any directory with Mesa importable:

```bash
python path/to/datacollector_smoke.py
python path/to/scenario_smoke.py
```

Both scripts print JSON. Treat `"ok": true` as an installed-package sanity check, not as full project validation.
