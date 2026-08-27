---
name: hpo-and-mutation
description: "Use AgileRL evolutionary HPO, tournament selection, mutation
  probabilities, mutable hyperparameters, and population evolution safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL HPO And Mutation

Use this sub-skill when the task is about AgileRL evolutionary hyperparameter optimization (HPO), `TournamentSelection`, `Mutations`, `HyperparameterConfig`, `RLParameter`, mutation probabilities, architecture mutation behavior, or diagnosing why a population did or did not mutate.

## Read First

- `references/hpo-workflows.md` for the standard tournament + mutation loop.
- `references/api-reference.md` for key HPO classes and parameters.
- `references/troubleshooting.md` for invalid mutable attributes, probability, and architecture mutation failures.
- `scripts/inspect_hpo_setup.py --help` for a safe config-only HPO probe.

## Boundaries

- Training-loop placement belongs in `../training-workflows/SKILL.md`, `../multi-agent-and-wrappers/SKILL.md`, `../offline-bandits-data/SKILL.md`, or `../llm-fine-tuning/SKILL.md` depending on the workflow.
- Architecture object construction belongs in `../evolvable-modules/SKILL.md`.
- This sub-skill owns which hyperparameters are mutable, how mutation probabilities are selected, how tournament selection preserves elites, and why mutation may be a no-op.

## Standard HPO Flow

1. Create a population of AgileRL agents.
2. Evaluate population fitness.
3. Select elites and the next generation with `TournamentSelection`.
4. Mutate offspring with `Mutations`.
5. Continue training with the evolved population.

```python
from agilerl.hpo.tournament import TournamentSelection
from agilerl.hpo.mutation import Mutations
from agilerl.algorithms.core.registry import HyperparameterConfig, RLParameter

hp_config = HyperparameterConfig(
    lr=RLParameter(min=1e-4, max=1e-2),
    batch_size=RLParameter(min=32, max=256),
    learn_step=RLParameter(min=1, max=10, grow_factor=1.5, shrink_factor=0.75),
)

tournament = TournamentSelection(tournament_size=2, elitism=True, population_size=6, eval_loop=1)
mutations = Mutations(
    no_mutation=0.4,
    architecture=0.2,
    new_layer_prob=0.2,
    parameters=0.2,
    activation=0.0,
    rl_hp=0.2,
    mutation_sd=0.1,
    rand_seed=1,
    device="cpu",
)
```

## Decision Points

- Set `activation=0` when activation mutations are unsupported or not desired.
- Use `HyperparameterConfig` fields that exactly match algorithm attributes.
- Keep `population_size`, `POP_SIZE`, and tournament population size aligned.
- Use deterministic seeds when comparing HPO behavior.
- For LLM algorithms, do not assume architecture mutations are supported.
