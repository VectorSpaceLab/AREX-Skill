---
name: network-modeling
description: "Build, mutate, validate, and migrate PyPSA Network component models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyPSA network-modeling sub-skill

Use this sub-skill when the task is to create or mutate a `pypsa.Network`: define buses, carriers, components, static and time-varying attributes, snapshots, investment periods, scenarios, component schemas, standard line/transformer types, and modeling-related options or consistency checks.

## Route here

- Build a network from scratch with `pypsa.Network()` and `n.add(...)`/`n.remove(...)`.
- Inspect or edit component tables through `n.components`, `n.c`, `n.generators`, `n.generators_t`, or the new Components API.
- Decide whether attributes are static, time-varying, scenario-specific, or period-specific.
- Define carriers, buses, generators, loads, lines, links, stores, storage units, transformers, standard types, and global constraints as model inputs.
- Run `n.consistency_check()`, `n.sanitize()`, `n.calculate_dependent_values()`, `n.copy()`, or `n.equals(...)` to validate the model structure before solving.

## Route away

- Import/export, CSV/netCDF/HDF5/Excel/cloud paths, and example-network caching belong to [network-io-data](../network-io-data/SKILL.md).
- `n.optimize(...)`, Linopy models, solver choices, linear/nonlinear power flow, and infeasibility tracing belong to [optimization-powerflow](../optimization-powerflow/SKILL.md).
- Statistics, plotting, clustering, maps, charts, and `NetworkCollection` analysis belong to [analysis-visualization](../analysis-visualization/SKILL.md).

## Operating loop

1. Create the network and define snapshots before adding time-varying data.
2. Add explicit `Carrier` rows for every bus carrier and technology carrier to avoid undefined-carrier warnings.
3. Add `Bus` rows before components that reference them; use `Link` for controllable cross-carrier conversion and `Line`/`Transformer` for passive electric branches.
4. For multiple components with time-varying data, pass a `DataFrame` whose index is exactly `n.snapshots` and whose columns are exactly the component names.
5. Validate with `n.consistency_check(...)`; use `n.sanitize()` only when adding missing buses/carriers and deterministic carrier colors is acceptable.
6. Route to optimization or analysis only after the network structure and time-series shapes are clean.

## Runtime references and helper

- [API reference](references/api-reference.md) explains verified constructor/mutation signatures, Components-store access, old/new API migration points, and static-vs-dynamic shape rules.
- [Component patterns](references/component-patterns.md) gives self-contained recipes for buses, carriers, one-port components, branches, storage, sector coupling, standard types, periods, and scenarios.
- [Options and consistency](references/options-and-consistency.md) covers modeling-relevant PyPSA options, scoped `option_context` use, consistency checks, `sanitize`, and stochastic/multi-period validation.
- [Troubleshooting](references/troubleshooting.md) maps common modeling warnings and errors to concrete fixes, including DataFrame shape mismatches and Components API deprecations.
- [Build tiny network helper](scripts/build_tiny_network.py) creates a deterministic self-contained network with carrier rows, optional time series, optional new Components API access, and optional consistency checks.
