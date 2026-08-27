# Mesa Example Pattern Index

## When to read

Read this when a user asks for a classic Mesa example model, asks which pattern to imitate, or provides a domain description and needs routing to the right sub-skill. This index distills the example-library patterns into self-contained guidance; do not require future agents to open the original example files.

## Basic patterns

| Example pattern | Use it for | Skill route | Key ingredients |
| --- | --- | --- | --- |
| Boltzmann wealth exchange | First Mesa model, random agent activation, simple scalar agent state, DataCollector output | [model-core](../sub-skills/model-core/SKILL.md) + [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) | `Model`, `Agent`, `AgentSet.shuffle_do`, agent wealth variable, model reporter such as Gini/mean wealth |
| Schelling segregation | Grid placement, movement to empty cells, local-neighborhood satisfaction, simple spatial dashboard | [spaces](../sub-skills/spaces/SKILL.md) + [visualization](../sub-skills/visualization/SKILL.md) | `OrthogonalMooreGrid`, `CellAgent`, `empties`, agent portrayal by type/happiness |
| Conway's Game of Life | Cell/patch agents, staged update (`step` then `advance`), grid-wide state transitions | [model-core](../sub-skills/model-core/SKILL.md) + [spaces](../sub-skills/spaces/SKILL.md) | fixed cell agents, neighbor counts, simultaneous/staged activation |
| Virus on network | Graph-based interaction model, state transitions over network neighbors | [spaces](../sub-skills/spaces/SKILL.md) | `Network`, optional `networkx`, per-agent state enum, neighbor contacts |
| Boid flockers | Continuous movement, local neighbor queries, vector-like position/heading behavior | [spaces](../sub-skills/spaces/SKILL.md) | experimental `ContinuousSpace`, neighbor radius, torus correction, model RNG |

## Advanced patterns

| Example pattern | Use it for | Skill route | Key ingredients |
| --- | --- | --- | --- |
| Wolf-sheep predation | Predator/prey/resource dynamics, property layers or fixed resource patches, multiple agent types | [model-core](../sub-skills/model-core/SKILL.md), [spaces](../sub-skills/spaces/SKILL.md), [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) | type-specific activation, reproduction/removal, data reporters by species |
| Epstein civil violence | Scenario parameters, multiple interacting classes, stateful outcomes | [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) | `Scenario`, agent state classes, cops/citizens, output reporters |
| Prisoner's dilemma grid | Grid-local repeated interactions and neighbor strategy updates | [spaces](../sub-skills/spaces/SKILL.md) | cell neighbors, strategy/payoff attributes, activation rounds |
| Sugarscape | Resource layers, capacity/availability, trading or neighborhood search | [spaces](../sub-skills/spaces/SKILL.md) + [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) | property layers, spatial search, model/agent reporters |

## Experimental patterns

| Example pattern | Use it for | Skill route | Key ingredients |
| --- | --- | --- | --- |
| Alliance formation | Multi-level/meta-agent analysis and network relationships | [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) | `MetaAgent`-style grouping, graph-like relations, power/position attributes |
| Tram route | Timed action/state behavior and custom visualization | [analysis-experiments](../sub-skills/analysis-experiments/SKILL.md) + [visualization](../sub-skills/visualization/SKILL.md) | experimental actions/states, custom Matplotlib drawing, state-dependent portrayal |

## Choosing a starting pattern

- If the task is mostly **agent lifecycle and activation**, start with Boltzmann wealth or Conway-style patterns, then read `model-core`.
- If it is mostly **space topology or movement**, choose Schelling, virus/network, boids/continuous, or Sugarscape-style patterns, then read `spaces`.
- If it is mostly **outputs and experiments**, choose Wolf-sheep, Epstein, or scenario-style patterns, then read `analysis-experiments`.
- If it is mostly **dashboard behavior**, combine the owning model/space/data sub-skill with `visualization` rather than treating the dashboard as the model definition.

## Avoid copying complete examples blindly

Use these examples as patterns, not as source dependencies. Rebuild the minimal model objects, spaces, reporters, and visualization components needed for the user's task; then validate them with the bundled smoke scripts and task-specific assertions.
