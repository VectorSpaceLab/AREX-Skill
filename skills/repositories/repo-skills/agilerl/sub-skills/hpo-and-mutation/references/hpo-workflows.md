# HPO Workflows

## Tournament Selection

`TournamentSelection` chooses agents for the next generation. With elitism, the best evaluated agent is preserved automatically. Other survivors come from tournaments of size `tournament_size`, where the best fitness in each sampled group wins.

Use:

```python
tournament = TournamentSelection(
    tournament_size=2,
    elitism=True,
    population_size=INIT_HP["POP_SIZE"],
    eval_loop=1,
)
```

`eval_loop` controls how many recent fitness values are considered when comparing agents.

## Mutations

`Mutations` applies population-level exploration. Important probabilities:

- `no_mutation`: leave offspring unchanged.
- `architecture`: mutate evolvable architecture.
- `new_layer_prob`: bias architecture mutations toward new layers.
- `parameters`: mutate network weights.
- `activation`: change activation functions when supported.
- `rl_hp`: mutate registered RL hyperparameters.

The mutation standard deviation (`mutation_sd`) controls Gaussian perturbation strength for parameter mutations.

## Mutable RL Hyperparameters

Use `HyperparameterConfig` and `RLParameter` to tell AgileRL which algorithm attributes can mutate.

```python
from agilerl.algorithms.core.registry import HyperparameterConfig, RLParameter

hp_config = HyperparameterConfig(
    lr=RLParameter(min=1e-4, max=1e-2),
    batch_size=RLParameter(min=8, max=512),
    learn_step=RLParameter(min=1, max=120, grow_factor=1.5, shrink_factor=0.75),
)
```

The field names must match attributes on the algorithm object. If an algorithm has `lr_actor` and `lr_critic`, using `lr` may not mutate the intended value.

## Architecture Mutations

Architecture mutations operate on registered evolvable modules/networks. In classical RL, algorithms register network groups so mutation can apply corresponding changes to policy, critic, target, or grouped networks. Multi-agent mutation must account for homogeneous agent groups and centralized/decentralized networks. LLM algorithms do not generally support architecture mutations.

## Reproducibility

- Set `rand_seed` in `Mutations`.
- Set framework/environment seeds when available.
- Keep evaluation windows and tournament size stable when comparing runs.
- Log mutation outcomes and elite selection decisions for debugging.
