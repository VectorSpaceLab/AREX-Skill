---
name: integrations-and-backends
description: "Guides fg-data-profiling Spark, notebook, streaming, interactive
  app, optional dependency, and migration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integrations and Backends

Use this sub-skill when the request is about Spark DataFrames, notebook widgets,
optional dependencies, streaming snapshots, interactive apps, PyCharm setup, or
other backend readiness work around fg-data-profiling.

## Read first

- Read [references/integrations.md](references/integrations.md) for the package
  integration landscape and migration notes.
- Read [references/spark-backend.md](references/spark-backend.md) for Spark
  prerequisites, supported features, and current limitations.
- Read [references/optional-dependencies.md](references/optional-dependencies.md)
  for notebook, Unicode, and other extras.
- Read [references/troubleshooting.md](references/troubleshooting.md) for Java,
  PySpark, widget, and legacy-integration errors.
- Run [scripts/check_spark_readiness.py](scripts/check_spark_readiness.py) when
  you need a safe status-only report for Spark readiness before choosing a
  Spark-specific workflow.

## Supported integration families

| Family | Use case |
| --- | --- |
| Spark DataFrames | Optional profiling of large distributed datasets when Java/PySpark are available |
| Notebook widgets | Rich notebook display and interactive widgets with `ipywidgets` |
| Bytewax / streaming | Profiling repeated snapshots of stream windows |
| Dash / Streamlit / Panel | Embedding HTML report outputs inside apps |
| PyCharm / IDE tools | External tool invocations using the installed CLI |
| Great Expectations | Legacy expectation-suite generation caveat and dependency handling |
| Unicode enrichment | Optional richer Unicode script/block naming |
| Migration from `ydata_profiling` | Compatibility import warning and rename guidance |

## Core boundary

- Core profile generation belongs in
  [../profiling-workflows/SKILL.md](../profiling-workflows/SKILL.md).
- CLI command shapes belong in
  [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md).
- Settings/output behavior belongs in
  [../configuration-and-output/SKILL.md](../configuration-and-output/SKILL.md).
- Comparison/privacy details belong in
  [../comparison-and-quality/SKILL.md](../comparison-and-quality/SKILL.md).

## Spark honesty

The package has first-class Spark code paths, but the creation environment did
not contain Java or PySpark. Do not claim Spark runtime verification unless the
user's environment has been checked with the bundled readiness script and the
selected Spark tests or smoke checks have been run.

## Preferred starting point

If a user is uncertain whether their backend is ready, start with the readiness
script and the import name they already have installed:

```bash
python scripts/check_spark_readiness.py
```

Only move into Spark DataFrame profiling after the readiness report says the
Java/PySpark stack is present.
