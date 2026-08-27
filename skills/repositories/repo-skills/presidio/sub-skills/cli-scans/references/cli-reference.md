# CLI reference

## Entry point

- Console script: `presidio`
- Installed command target: `presidio_cli.cli:run`
- Config helper: `PresidioCLIConfig`

## Current usage shape

```text
presidio [-h] [-v] [-] [-c CONFIG_FILE | -d CONFIG_DATA]
         [-f {standard,github,auto,colored,parsable}]
         [--no-warnings] [--threshold THRESHOLD]
         [FILE_OR_DIR ...]
```

- `FILE_OR_DIR...` scans one or more files or directories.
- `-` reads from standard input.
- `-c/--config-file` loads a YAML file.
- `-d/--config-data` loads YAML text directly from the command line.
- `-f/--format` selects the output formatter.
- `--no-warnings` hides warning-level findings.
- `--threshold` overrides the loaded threshold for the current run only.

## Scan behavior

- Directories are walked recursively.
- Files are treated as text only when they decode cleanly as UTF-8.
- Binary-like files are skipped.
- Ignore rules are applied through the loaded config.
- Stdin is analyzed as a stream and is not matched against filesystem ignore rules.

## Output formats

| Format | Behavior | Best use |
| --- | --- | --- |
| `standard` | Plain file header followed by `line:column score entity` rows. | Local review and quick human checks. |
| `colored` | Same as standard, with ANSI colors when stdout is a TTY. | Interactive terminals. |
| `github` | GitHub annotation groups with file, line, and column metadata. | CI logs and pull-request annotations. |
| `parsable` | One JSON object per finding. | Scripts, parsers, and downstream automation. |
| `auto` | `github` on GitHub Actions, `colored` in a TTY, otherwise `standard`. | Default local behavior. |

### GitHub format shape

- Uses `::group::filename` and `::endgroup::` wrappers.
- Emits annotation lines with `file=...`, `line=...`, and `col=...`.
- Keep it for environments that understand GitHub Actions annotations.

### Parsable format shape

- Emits line-delimited JSON.
- Each line is the serialized `RecognizerResult` dictionary.
- Do not expect file headers or summary lines.

## Common command patterns

```bash
# Scan a directory with a bundled template
presidio -c scripts/sample_presidiocli.yaml src/

# Scan stdin
printf 'John Smith\n' | presidio -

# CI-friendly annotations
presidio -c scripts/sample_presidiocli.yaml --format github --threshold 0.7 --no-warnings src/

# Machine-parsable output
presidio -c scripts/sample_presidiocli.yaml --format parsable src/
```

## Configuration shortcuts

- `--config-data` is useful for short inline YAML snippets.
- When the inline value has no colon, the CLI treats it as `extends: <value>`.
- `.presidiocli` is read only from the current working directory.
- The bundled config fallback is `extends: default`.

## When to route elsewhere

If you need to change recognizers, model selection, or supported entity behavior, use `../analyze-text/SKILL.md` instead of the CLI layer. If you need to transform findings into replacements, use `../anonymize-text/SKILL.md`.