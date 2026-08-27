---
name: configuration-and-output
description: "Guides fg-data-profiling Settings, YAML config, environment
  variables, report sections, HTML assets, cache, and serialization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Configuration and Output

Use this sub-skill when a user wants to control report contents, performance,
HTML rendering, YAML settings, environment variables, cache invalidation, or
serialization.

## Read first

- Read [references/configuration-reference.md](references/configuration-reference.md)
  for `Settings`, shorthands, config-file patterns, and important field names.
- Read [references/output-and-rendering.md](references/output-and-rendering.md)
  for HTML/JSON files, local assets, CDN mode, themes, SVG/PNG plots, and
  notebook-related output decisions.
- Read [references/cache-and-serialization.md](references/cache-and-serialization.md)
  for `invalidate_cache()`, `dump()`, `load()`, and `.pp` serialized reports.
- Read [references/troubleshooting.md](references/troubleshooting.md) for common
  config/output failures.
- Run [scripts/write_minimal_config.py](scripts/write_minimal_config.py) when a
  user asks for a safe starter YAML config for large or privacy-sensitive data.

## Common configuration routes

| User intent | Start with |
| --- | --- |
| Large dataset, faster report | `minimal=True`, a minimal YAML, or disable correlations/interactions/missing diagrams/samples/duplicates |
| Privacy-aware report sections | `samples=None`, `duplicates=None`, sensitive workflow in comparison/quality sub-skill |
| Branded HTML report | `html={"style": {"theme": "flatly", "primary_colors": [...]}}` and output reference |
| External assets instead of inline HTML | `html={"inline": False}` and preserve the generated assets directory |
| Programmatic settings object | `from data_profiling.config import Settings` and mutate before report computation |
| Environment-variable control | Use `PROFILE_`-prefixed variables, for example `PROFILE_TITLE` or JSON-valued `PROFILE_PLOT` |
| Re-render after changing config | `profile.invalidate_cache()` or construct a new `ProfileReport` |

## Key source-verified field names

Use current source names. In particular, categorical frequency plot settings
live under `plot.cat_freq`, not stale `plot.pie` naming.

```python
profile = ProfileReport(
    df,
    title="Configured profile",
    samples=None,
    correlations=None,
    missing_diagrams=None,
    duplicates=None,
    interactions=None,
    plot={"cat_freq": {"show": False}},
    html={"inline": False, "style": {"theme": "united"}},
)
```

## YAML config pattern

Use a YAML config when the same settings should be reused by API and CLI.
Do not combine a config file with `minimal=True` or CLI `--minimal`.

```python
profile = ProfileReport(df, config_file="profiling-config.yml")
```

```bash
data_profiling --silent --config_file profiling-config.yml data.csv report.html
```

## Boundaries

- Core report API usage belongs in
  [../profiling-workflows/SKILL.md](../profiling-workflows/SKILL.md).
- CLI flags and batch command shapes belong in
  [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md).
- Sensitive redaction policy and comparison output belong in
  [../comparison-and-quality/SKILL.md](../comparison-and-quality/SKILL.md).
- Optional Spark/notebook readiness belongs in
  [../integrations-and-backends/SKILL.md](../integrations-and-backends/SKILL.md).

## Validation

When generating settings for a user, prefer the bundled config writer or a small
snippet that parses with `Settings.from_file()`. For output behavior, create a
tiny local DataFrame and verify that the expected HTML/JSON file and assets
exist before using the same settings on real data.
