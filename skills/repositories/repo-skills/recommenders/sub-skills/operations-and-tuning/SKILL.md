---
name: operations-and-tuning
description: "Plan Microsoft Recommenders parameter sweeps, benchmark
  interpretation, optional backend readiness, and cloud operationalization
  without unsafe side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Operations and Tuning

Use this sub-skill when a user asks about hyperparameter grids, NNI or AzureML tuning patterns, benchmark loops, Databricks/AzureML/AKS operationalization, service sizing, optional backend readiness, or why a Recommenders environment cannot run a workflow.

## Backend truth for this skill

- Verified in the base CPU scope: `generate_param_grid`, K8s sizing utility signatures, package import diagnostics, and safe optional-module probes.
- Optional and not verified in this CPU scope: NNI service workflows, AzureML HyperDrive, Databricks cluster installation, AKS load tests, Spark benchmark jobs, and GPU/deep-learning benchmarks.
- Cloud and cluster scripts can mutate external state. Treat them as reference workflows until credentials, target resources, and user approval are explicit.

## Start here

- For local parameter sweep and NNI/AzureML tuning concepts, read [workflows.md](references/workflows.md).
- For Databricks, AzureML, AKS, Cosmos DB, and service sizing guidance, read [operationalization.md](references/operationalization.md).
- For benchmark loop structure and safe alternatives to full benchmark notebooks, read [benchmarking.md](references/benchmarking.md).
- For environment/backend/cloud failure modes, read [troubleshooting.md](references/troubleshooting.md).
- To collect a safe local readiness report without installing or mutating anything, run:

```bash
python sub-skills/operations-and-tuning/scripts/environment_report.py --check-optional
```

Run from the generated skill root, or adapt the script path to the installed skill location.

## Route elsewhere

- Dataset schemas, splitters, sparse matrices, and negative sampling belong in [data-preparation](../data-preparation/SKILL.md).
- Model family selection and fit/predict/recommend flows belong in [modeling](../modeling/SKILL.md).
- Metric definitions and direct metric calls belong in [evaluation](../evaluation/SKILL.md).

## Working rules

1. Separate a safe plan from an execution request. Tuning and cloud scripts often need data, credentials, compute targets, or long runtime.
2. Start with a bounded local parameter grid before escalating to NNI, AzureML, or full benchmarks.
3. Treat Spark/GPU/cloud readiness as a gate: package extras, system runtime, hardware, data, and credentials must all be checked.
4. Do not run Databricks, AzureML, AKS, or DBFS mutation commands unless the user explicitly asks and provides target details.
5. For benchmark claims, report hardware/backend/data size and skipped optional model families.
