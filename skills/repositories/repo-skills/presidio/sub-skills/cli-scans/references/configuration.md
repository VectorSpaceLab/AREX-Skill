# Configuration reference

## Load order

`PresidioCLIConfig` is resolved in this order:

1. `--config-data`
2. `--config-file`
3. `.presidiocli` in the current working directory
4. bundled default config via `extends: default`

`--config-data` is parsed as YAML text. If the supplied string has no colon, the CLI rewrites it to `extends: <value>` before loading.

## Config object

`PresidioCLIConfig(content=..., file=...)` loads YAML into these fields:

- `language`: language code passed to the analyzer, default `en`
- `entities`: list of Presidio Analyzer entity names to keep
- `ignore`: multi-line ignore patterns
- `allow_list`: allow-list tokens passed to the analyzer
- `threshold`: minimum score kept by the CLI
- `locale`: locale string passed to `locale.setlocale`
- `analyzer`: the internal `AnalyzerEngine` instance

## YAML keys

| Key | Type | Notes |
| --- | --- | --- |
| `language` | string | Expected language for detection. |
| `entities` | list[string] | Supported entity names only. Omit the key to use the analyzer's supported entity set. |
| `ignore` | multi-line string | Parsed with `pathspec` in `gitwildmatch` mode. |
| `allow` | list[string] | Exact tokens that should not be flagged. |
| `threshold` | number | Findings are kept when `score >= threshold`. The CLI flag `--threshold` overrides this value for one run. |
| `locale` | string | Applied with `locale.setlocale(locale.LC_ALL, locale)`. |
| `extends` | string | Loads a bundled name such as `default` or `limited`, or a file path. |

## Merge and resolution notes

- Bundled names such as `default` and `limited` resolve from the package config directory when available.
- Custom paths are used as-is.
- `extends` merges entity lists, while base language and ignore values can override the current config.
- Entity names are validated against Presidio Analyzer's supported entity catalog during config load.
- The current directory is the only place where `.presidiocli` is auto-discovered.

## Example template

```yaml
language: en
entities:
  - PERSON
  - EMAIL_ADDRESS
ignore: |
  .git
  *.cfg
allow:
  - "example@example.com"
threshold: 0.75
# locale: en_US.UTF-8
# extends: default
```

## When to route elsewhere

If you need to add custom recognizers, filters, or NLP backends, move to `../analyze-text/SKILL.md`. If you need anonymization instead of scanning, move to `../anonymize-text/SKILL.md`.