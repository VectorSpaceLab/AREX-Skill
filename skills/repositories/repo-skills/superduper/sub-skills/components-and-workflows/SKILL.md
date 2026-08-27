---
name: components-and-workflows
description: "Compose Superduper components, callable models, listeners,
  training scaffolds, applications, and lightweight workflow patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Components and Workflows

Use this sub-skill when a task involves composing Superduper AI workflows from components: `Component`, `ObjectModel`, `Model`, `Dataset`, `Metric`, `Validation`, `Trainer`, `Listener`, `Application`, `CronJob`, `FunctionCronJob`, or `Streamlit`.

## Route Here For

- Choosing component identifiers and `upstream` dependencies for multi-step workflows.
- Wrapping Python callables or object methods as `ObjectModel` instances.
- Calling `predict` and `predict_batches` with the key shape expected by a model signature.
- Building listeners that read a table/query key and write model outputs to managed output tables.
- Applying components with `db.apply(...)`, including chained listeners and grouped applications.
- Sketching training, validation, metric, dataset, cron, Streamlit, and simple RAG-like component layouts.
- Diagnosing workflow composition errors around identifiers, callable serialization, listener keys/selects, output naming, and downstream datatype mismatches.

## Route Elsewhere

- Nearest-neighbor/vector-index setup, vector search measures, and `table.like(...)` retrieval belong in `vector-search-and-retrieval`.
- Plugin/provider installation, credentials, service daemons, and provider-specific optional dependencies belong in `plugins-and-integrations`.
- Connection strings, artifact stores, config files, metadata stores, and low-level Datalayer setup belong in `datalayer-and-config`.

## Required Reading

1. For component, model, listener, training, validation, and UI/API constructor behavior, read [references/components-models-listeners.md](references/components-models-listeners.md).
2. For end-to-end workflow patterns, `db.apply(...)`, listener chaining, `Application` grouping, and simplified RAG structure, read [references/workflows.md](references/workflows.md).
3. For common failure modes and repair actions, read [references/troubleshooting.md](references/troubleshooting.md).
4. For a safe local construction/prediction smoke helper, use [scripts/superduper_component_smoke.py](scripts/superduper_component_smoke.py).

## Quick Operating Checklist

- Give every component a stable, non-empty `identifier`; use readable lowercase or snake/kebab names for workflow pieces.
- Represent prerequisites explicitly with `upstream=[...]`, especially for downstream listeners that read upstream listener output fields.
- Prefer `ObjectModel(identifier=..., object=top_level_callable, datatype=...)` for deterministic local components.
- Match a listener's `key` shape to the wrapped model signature before applying it.
- Use `listener.outputs` as the downstream document field name and `listener.predict_id` when a query API asks for an output id.
- Apply source tables/data before listeners that need a `select`; use `jobs=False` only when you want to register components without running jobs.
- Keep vector nearest-neighbor details, provider credentials, and low-level config out of this route.
