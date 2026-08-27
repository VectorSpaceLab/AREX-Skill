# HPO API Reference

## `TournamentSelection`

Verified constructor shape:

```python
TournamentSelection(tournament_size: int, elitism: bool, population_size: int, eval_loop: int)
```

Important methods include selection over a population with fitness history. Use it after evaluation and before mutation.

## `Mutations`

`Mutations` configures no-op, architecture, new-layer, parameter, activation, and RL hyperparameter mutation probabilities. Common constructor arguments include:

- `no_mutation`
- `architecture`
- `new_layer_prob`
- `parameters`
- `activation`
- `rl_hp`
- `mutation_sd`
- `rand_seed`
- `device`

Inspect the installed package or source for the exact version-specific constructor when writing production code.

## `HyperparameterConfig` And `RLParameter`

`HyperparameterConfig` is a dataclass-like container whose fields map to mutable algorithm attributes. `RLParameter` stores value ranges and optional grow/shrink factors.

Common mutable fields:

- `lr`
- `batch_size`
- `learn_step`
- algorithm-specific learning rates or coefficients when exposed as attributes

## Mutation Registry

AgileRL algorithms inherit from evolvable algorithm bases that register:

- Mutable network groups for architecture/parameter mutation.
- Hyperparameter config for RL hyperparameter mutation.
- Optimizer wrappers linked to mutable networks.

For custom algorithms, register network groups and optimizer wrappers in `__init__` so mutation can discover them.
