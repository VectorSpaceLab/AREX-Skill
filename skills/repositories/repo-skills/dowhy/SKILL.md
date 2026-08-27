---
name: dowhy
description: "Route DoWhy causal inference, graphical causal model, and
  graph/data workflows to the right sub-skill and bundled references."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DoWhy

Use this repo skill for the `dowhy` Python package. It is a router for the
package's main user-facing workflows, not a full manual.

## Start here

If the user names the package but not a specific workflow, read
[references/package-overview.md](references/package-overview.md) first. It
maps the public modules to the right sub-skill.

## Route map

- Classic causal effect estimation, identification, refutation, or `CausalModel`
  workflows belong in
  [sub-skills/effect-estimation/SKILL.md](sub-skills/effect-estimation/SKILL.md).
- Graphical causal models, mechanisms, interventions, counterfactuals,
  anomaly attribution, distribution change, and validation belong in
  [sub-skills/graphical-causal-models/SKILL.md](sub-skills/graphical-causal-models/SKILL.md).
- Graph parsing, graph/data alignment, pandas `.causal.do`, do-samplers,
  datasets, plotting backends, and temporal helpers belong in
  [sub-skills/data-graph-interfaces/SKILL.md](sub-skills/data-graph-interfaces/SKILL.md).
- Optional integrations and boundary features such as causal prediction,
  TabPFN, EconML/CausalML wrappers, graph discovery wrappers, `pydot`, and
  `pygraphviz` belong in
  [references/optional-integrations.md](references/optional-integrations.md).
- Cross-cutting install/import and workflow confusion goes to
  [references/troubleshooting.md](references/troubleshooting.md).

## Install and quick smoke check

The public package install is:

```bash
python -m pip install dowhy
```

If the user needs plotting, graph parsing, or optional estimators, read
[references/optional-integrations.md](references/optional-integrations.md)
first because some extras are version-sensitive or require external packages.

A quick runtime sanity check is:

```bash
python -c "import dowhy, dowhy.gcm; from dowhy import CausalModel; print(dowhy.__version__)"
```

For a broader environment probe, run:

```bash
python scripts/check_dowhy_environment.py
```

If you are working on a local checkout rather than using a published wheel,
install from the checkout with an editable install before editing the package,
but keep that contributor workflow separate from the runtime guidance here.

## How to choose the right path

1. If the user wants an effect estimate or robustness check, stay in
   `effect-estimation`.
2. If the user wants generated samples, interventions, counterfactuals, or
   causal influence from a fitted graph model, use `graphical-causal-models`.
3. If the user first needs to build, parse, or align a graph and DataFrame,
   use `data-graph-interfaces` and then route downstream.
4. If the user is asking about an optional dependency, treat it as a boundary
   question, not a core workflow failure, unless the task explicitly requires
   that optional package.
5. If the user only wants to know whether this skill matches their checkout,
   read `references/repo-provenance.md`.

## What this skill covers well

- `CausalModel` construction, identification, estimation, `do`, and refutation.
- `dowhy.gcm` model classes, mechanism assignment, sampling, attribution, and
  validation.
- Graph parsing and graph/DataFrame setup needed by both core workflows.
- Optional integration boundaries and troubleshooting for missing extras.

## What this skill does not try to do by itself

- It does not replace the sub-skills above with one giant manual.
- It does not claim optional integrations are always installed.
- It does not require the original checkout once the bundled skill files exist.
- It does not describe repo test or review artifacts; those live under
  `skills/tests/dowhy/`.

## Reference map

- [references/package-overview.md](references/package-overview.md) for the
  module-to-workflow map.
- [references/optional-integrations.md](references/optional-integrations.md)
  for optional packages, extras, and boundary features.
- [references/troubleshooting.md](references/troubleshooting.md) for the most
  common cross-cutting failures and the best next check.
- [references/repo-provenance.md](references/repo-provenance.md) when checking
  whether this skill is current for the present checkout.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  for router metadata used by the managed repo-skill importer.
- [scripts/check_dowhy_environment.py](scripts/check_dowhy_environment.py) for
  a small environment probe that reports core and optional imports.

## Response style

When routing a user question, name the sub-skill, state the core package object
or workflow family, and give one validation or troubleshooting check. If the
question is about an optional integration, say so explicitly and mention the
likely dependency boundary.
