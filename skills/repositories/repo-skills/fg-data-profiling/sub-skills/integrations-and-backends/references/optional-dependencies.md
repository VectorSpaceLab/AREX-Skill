# Optional Dependencies Reference

## When to read

Read this when a workflow needs notebook widgets, Unicode enrichments, or other
optional package extras.

## Notebook widgets

The `notebook` extra enables richer notebook display and widgets. If the package
is installed but the notebook only shows plain text such as `IntSlider(value=0)`,
the widget frontend likely is not enabled in the environment.

Fallbacks:
- `profile.to_notebook_iframe()` for HTML notebook embedding
- `profile.to_file("report.html")` for a portable HTML report

## Unicode enrichment

The `unicode` extra adds richer script/block naming through
`tangled_up_in_unicode`. When it is missing, the package falls back to Python's
standard Unicode categories and basic names.

## Image and text extras already in the base install

The base package already pulls in image- and text-related dependencies such as
`imagehash` and `wordcloud` through its runtime dependencies. Do not install the
dev/doc/test groups just to use normal image or text profiling.

## Great Expectations

The docs explicitly say the current package versions no longer support the full
Great Expectations integration that older examples demonstrated. If a user asks
for expectation-suite generation, treat it as a legacy compatibility surface and
route the actual dependency/version decision to the user.

## Readiness hints

Use the following checks before making integration claims:

```python
import importlib.util
print(importlib.util.find_spec("ipywidgets") is not None)
print(importlib.util.find_spec("tangled_up_in_unicode") is not None)
print(importlib.util.find_spec("great_expectations") is not None)
```

For Spark, use the Spark backend reference instead of trying to infer readiness
from the notebook or Unicode extras.
