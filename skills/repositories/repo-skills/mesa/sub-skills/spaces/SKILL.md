---
name: spaces
description: "Build and troubleshoot Mesa discrete and experimental continuous
  spaces, including grids, networks, Voronoi cells, property layers, and
  movement agents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Spaces

Use this sub-skill for Mesa's modern space APIs: `mesa.discrete_space` and `mesa.experimental.continuous_space`.

## Use for

- `Cell`, `CellCollection`, `DiscreteSpace`, and the grid/network/voronoi space families.
- `CellAgent`, `FixedAgent`, and `Grid2DMovingAgent` movement and occupancy logic.
- Property layers, `cells_with_capacity`, `empties`, and capacity-limited placement.
- `ContinuousSpace` and `ContinuousSpaceAgent` for experimental continuous movement.
- Safe smoke checks against an installed Mesa package.

## Route elsewhere

- Model lifecycle, activation, and scheduling: [../model-core/SKILL.md](../model-core/SKILL.md)
- Data collection, scenarios, and experiment runs: [../analysis-experiments/SKILL.md](../analysis-experiments/SKILL.md)
- Visualization and rendering of space layers: [../visualization/SKILL.md](../visualization/SKILL.md)

## Start here

1. Read [references/api-reference.md](references/api-reference.md) for verified signatures and object relationships.
2. Use [references/workflows.md](references/workflows.md) for copyable recipes.
3. Check [references/troubleshooting.md](references/troubleshooting.md) for common failures and fixes.
4. Run [scripts/space_smoke.py](scripts/space_smoke.py) for a safe runtime probe.

## High-signal rules

- Import modern space APIs from `mesa.discrete_space` and `mesa.experimental.continuous_space`.
- Do not use legacy `mesa.space` for new work.
- Use `cells_with_capacity` for partially full cells; `empties` only when you need zero occupancy.
- Mutate property layers in place. Do not rebind `grid.<layer>` to a new array.
- Use seeded randomness (`Model(rng=seed)` or `random.Random(seed)`) for repeatable layouts.
- Prefer `CellAgent` for mobile occupancy, `FixedAgent` for one-time placement, and `Grid2DMovingAgent` for 2D directional movement.
- Keep `networkx` optional in user-facing code; only build `Network` examples when the graph stack is available or when you provide an explicit layout.
- Use `ContinuousSpaceAgent.remove()` and `CellAgent.remove()` rather than mutating registries directly.
