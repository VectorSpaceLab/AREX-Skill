# R Wrapper and MLOps Integration Notes

## When to read

Read this when a user asks whether this AIF360 skill covers the R package,
reticulate setup, Kubeflow samples, NiFi processors, or platform integration
assets.

## R package boundary

AIF360 includes an R package wrapper that exposes selected AIF360 capabilities
through R and reticulate. This generated skill is Python-focused and did not
verify an R runtime. Treat R workflows as reference-only unless the current task
explicitly prepares and verifies R.

Typical R setup concepts:

- Install the R package from CRAN or development source.
- Use reticulate to select or create the Python environment that contains
  `aif360`.
- Run the package's loading helper once the Python environment is configured.
- Restart the R session when R reports locked binding or reticulate state
  issues.

Before claiming R support in a downstream task, verify:

1. R is installed.
2. reticulate sees the intended Python.
3. Python imports `aif360` from that environment.
4. The selected R wrapper function runs on a tiny synthetic example.

## MLOps sample boundary

The repository includes platform-oriented examples for Kubeflow and NiFi. They
are not part of the verified Python package operating scope in this skill.

Treat them as integration samples when a user explicitly asks for:

- Kubeflow pipeline components or Docker images using AIF360 fairness checks.
- NiFi processors or flow assets that invoke AIF360.
- Platform deployment, Java/Maven builds, containers, or service integration.

Before acting on those workflows, verify the platform-specific runtime:

- Docker/Kubeflow availability and image build permissions.
- NiFi/Maven/Java versions and flow deployment target.
- Data locations, credentials, service endpoints, and write permissions.
- Whether the task is about using AIF360 APIs inside a platform or maintaining
  the platform integration code.

## Routing guidance

- For Python fairness metrics, mitigation, sklearn APIs, MDSS/FACTS, and metric
  explainers, stay in the main sub-skills.
- For R wrapper usage, treat this reference as a boundary note and verify R in
  the target environment before giving runnable commands.
- For Kubeflow/NiFi integration, do not rely on this Python package skill as a
  complete platform operations guide. Use it for AIF360 API semantics only.

## Long-tail gap

This skill intentionally does not provide a full R package skill or MLOps
platform skill. If future users repeatedly request AIF360 R or platform
operations, create or extend a dedicated skill after preparing those runtimes
and verifying representative cases.
