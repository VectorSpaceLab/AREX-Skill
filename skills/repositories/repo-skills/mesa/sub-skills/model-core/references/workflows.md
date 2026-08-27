# Workflows

## 1) First model

Use this pattern when you need a minimal Mesa model that creates agents and advances time.

```python
import mesa

class MoneyAgent(mesa.Agent):
    def __init__(self, model, wealth):
        super().__init__(model)
        self.wealth = wealth

    def step(self):
        self.wealth += 1

class MoneyModel(mesa.Model):
    def __init__(self, n=10, rng=None):
        super().__init__(rng=rng)
        initial_wealth = self.rng.integers(1, 5, size=n)
        MoneyAgent.create_agents(self, n, initial_wealth)

    def step(self):
        self.agents.shuffle_do("step")

model = MoneyModel(n=10, rng=42)
model.run_for(5)
```

Recipe:

1. Call `super().__init__(rng=rng)` in the model.
2. Call `super().__init__(model)` in each agent.
3. Create agents with `Agent.create_agents(...)` after the model is initialized.
4. Put activation logic in `step()`.
5. Use `run_for()` or `run_until()` to advance the model.

Validation signals:

- `len(model.agents) == n`
- each agent has a unique `unique_id`
- `model.time == 5.0` after `run_for(5)`

## 2) Activation patterns

### Sequential activation

```python
def step(self):
    self.agents.do("step")
```

### Random activation

```python
def step(self):
    self.agents.shuffle_do("step")
```

### Multi-stage activation

```python
def step(self):
    for stage in ["sense", "decide", "act"]:
        self.agents.do(stage)
```

### Activation by type

```python
def step(self):
    for klass in self.agent_types:
        self.agents_by_type[klass].shuffle_do("step")
```

### Filtered activation

```python
rich = self.agents.select(lambda a: a.wealth >= 5)
rich.shuffle_do("donate")
```

Choose `do()` when order should be stable, `shuffle_do()` when order should be randomized, and `select()` when only a subset should act.

## 3) Event scheduling

Use `schedule_event()` for one-off work and `schedule_recurring()` for repeated work.

```python
from mesa.time import Priority, Schedule

class EconomyModel(mesa.Model):
    def __init__(self, rng=None):
        super().__init__(rng=rng)
        self.tax_rate = 0.10
        self.schedule_event(self.tax_reform, at=5.0)
        self.schedule_event(self.stimulus, after=2.0, priority=Priority.HIGH)
        self.review = self.schedule_recurring(
            self.collect_taxes,
            Schedule(interval=3.0, start=3.0, count=4),
        )

    def tax_reform(self):
        self.tax_rate = 0.25

    def stimulus(self):
        for agent in self.agents:
            agent.wealth += 5

    def collect_taxes(self):
        for agent in self.agents:
            agent.wealth -= 1

    def step(self):
        self.agents.do("step")
```

Rules of thumb:

- Use `at=` for absolute time.
- Use `after=` for relative time from now.
- `Priority.HIGH` runs before default and low priority at the same timestamp.
- Use `stop()` on the returned `EventGenerator` to end a recurring schedule.
- Use `cancel()` on the returned `Event` to prevent a one-off callback.
- Advance time with `run_for()` or `run_until()` so scheduled work is processed.

Validation signals:

- one-off events fire once
- recurring generators stop after `count` or `end`
- `model.time` reaches the requested horizon
- event order at the same timestamp matches priority order

## 4) Lifecycle and removal

Use `agent.remove()` to delete an agent from the model.

```python
def cull_dead_agents(self):
    for agent in list(self.agents.select(lambda a: a.energy <= 0)):
        agent.remove()
```

When an agent owns external resources, override `remove()` and clean up before calling `super().remove()`.

```python
class TrackedAgent(mesa.Agent):
    def remove(self):
        self.cancel_action()
        super().remove()
```

For model-wide teardown, use `remove_all_agents()`.

Validation signals:

- `len(model.agents)` drops after removal
- removed agents disappear from `model.agents_by_type[...]`
- removed agents no longer receive activation calls

## 5) Reproducible RNG

Pick one reproducible seed path:

### Plain seed

```python
model = MyModel(rng=42)
```

### Scenario-backed seed

```python
from mesa.experimental.scenarios import Scenario

scenario = Scenario(rng=42, n_agents=10)
model = MyModel(scenario=scenario)
```

When you need deterministic per-agent initialization, draw values from `self.rng` and pass them through `create_agents()`.

```python
class MyModel(mesa.Model):
    def __init__(self, n=10, rng=None):
        super().__init__(rng=rng)
        start_values = self.rng.integers(0, 100, size=n)
        MyAgent.create_agents(self, n, start_values)
```

Rules:

- Use `self.rng` for NumPy draws.
- Use `self.random` for stdlib draws.
- Pass either `rng` or a `Scenario` instance, not both.
- If you already have a scenario class, let it own the random seed and read `self.rng` from the model.

Validation signals:

- repeated runs with the same seed produce the same initial values
- changing the seed changes the run deterministically
- `model.scenario.rng` and `model.rng` stay aligned when a scenario is used

## 6) Safe smoke loop

When you need a quick self-check, follow this sequence:

1. Build a tiny `Model` and `Agent` pair.
2. Register agents with `create_agents()`.
3. Schedule one one-off event and one recurring event.
4. Run with `run_for()`.
5. Confirm agent counts, event counts, and `model.time`.

That pattern is mirrored by [the bundled smoke script](../scripts/mesa_model_smoke.py).
