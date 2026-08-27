# Troubleshooting

## Invalid YAML or non-mapping config

**Symptom:** `invalid config: ...` or `invalid config: not a dict`

**Cause:** The config file or inline config is not valid YAML, or it parses to a scalar/list instead of a mapping.

**Fix:** Use a mapping document with indented keys. If you are using `--config-data`, make sure the string is real YAML and not a bare path unless you meant `extends: ...`.

## Unknown entity name

**Symptom:** `invalid config: no such entity X`

**Cause:** `entities` contains a name that Presidio Analyzer does not support.

**Fix:** Use supported entity names only, or omit `entities` to use the analyzer's supported set. If you need entity catalog work, route to `../analyze-text/SKILL.md`.

## Missing spaCy model or analyzer failure

**Symptom:** The scan fails when the default analyzer tries to start, or results are unexpectedly empty.

**Cause:** The CLI depends on the analyzer backend used by Presidio's default engine. If the documented English model is missing, the scan path may fail.

**Fix:** Install the documented language model or switch to a workflow that supplies the right analyzer backend. The CLI itself does not expose custom NLP engine selection.

## Ignore pattern surprises

**Symptom:** A file is not ignored, or an ignored tree still takes time to walk.

**Cause:** Ignore patterns use `gitwildmatch` syntax from `pathspec`, and directory traversal still walks the tree before analysis decides whether to skip a file.

**Fix:** Match against the CLI path form you are passing in, and use directory-aware patterns such as `.git` or `build/**`. If the tree is huge, narrow the scan root before invoking the CLI.

## Binary or very large directories

**Symptom:** The command is slow, or binary files do not appear in the output.

**Cause:** The CLI only scans text files that decode cleanly as UTF-8.

**Fix:** Let the binary skip behavior stand, but use ignore rules or smaller roots to avoid unnecessary recursion over generated content.

## Threshold looks wrong

**Symptom:** A finding appears or disappears unexpectedly.

**Cause:** Thresholding is inclusive: findings survive when `score >= threshold`. The `--threshold` flag overrides the loaded value for that run.

**Fix:** Re-check the configured threshold and remember that `--no-warnings` filters warning-level findings after scoring.

## GitHub or parsable output does not match expectations

**Symptom:** CI annotations are missing, or a parser cannot read the output.

**Cause:** `github` output is GitHub-annotation text, while `parsable` is line-delimited JSON with no file headers.

**Fix:** Use `--format github` inside GitHub Actions and `--format parsable` for automation that expects one JSON object per line.

## Stdin versus file arguments

**Symptom:** Paths are ignored, or ignore rules do not apply to piped text.

**Cause:** Stdin is scanned as an input stream, not as a filesystem path.

**Fix:** Use `presidio -` for piped text and file or directory arguments for filesystem scans. Ignore rules only apply to filesystem paths.

## `.presidiocli` is not picked up

**Symptom:** Your local config file seems to be ignored.

**Cause:** The CLI only looks for `.presidiocli` in the current working directory.

**Fix:** Run the command from the directory that contains the file, or pass `-c` explicitly.

## Locale errors

**Symptom:** `locale.Error` or unexpected locale-dependent formatting.

**Cause:** The configured `locale` is not installed on the host.

**Fix:** Remove the `locale` key or change it to a locale that exists on the machine.

## Exit code caveat from source

**Symptom:** The command prints findings but still exits with status 0.

**Cause:** The current source path does not accumulate a non-zero exit status from findings.

**Fix:** Treat the output as the source of truth, or wrap the CLI in your own guard if you need a hard-fail CI signal.