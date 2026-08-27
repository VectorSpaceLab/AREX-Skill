# Contribution Mirror Guidance

Use this reference only when a task asks about CausalNex's `contrib` area or repository contribution layout. It is not part of the normal runtime workflow for structure learning, Bayesian networks, discretization, or synthetic data.

## How to treat `causalnex.contrib`

- Treat `causalnex.contrib` as a contribution mirror/staging area, not as the primary public API surface for this skill.
- Do not place generated DisCo skill files under `causalnex/contrib`; keep generated runtime files in the configured generated skill directory and keep review artifacts outside the runtime skill tree.
- Contribution modules mirror ordinary package layout under a project namespace, for example `causalnex/contrib/<project>/plotting/...`.
- Matching contribution tests mirror that namespace under `tests/contrib/<project>/...`.
- Extra dependencies for contributed modules should be declared through package extras rather than silently becoming hard requirements for the base package.
- A contributed area should carry its own README-style usage note and enough tests to justify inclusion.

## Routing implication

If a future user asks how to add or review a contributed CausalNex module, answer from this reference and keep it separate from the operating sub-skills. If the task is about using existing graph-learning or Bayesian-network APIs, route to the relevant sub-skill instead.
