# CLI and Config Troubleshooting

## `--output` rejects a `.json` path

This checkout treats `--output` as an output directory and rejects paths whose
suffix is `.json` (case-insensitive). Use `--output annotations/` for a batch or
remove the extension from the target directory.

## `--config` says a file does not exist

A missing explicitly supplied path is fatal. Check the path before launch. A
missing default `~/.labelmerc` is non-fatal and uses built-in defaults.

## Inline YAML is not editable in Settings

Inline YAML has no file target. Put the same mapping in a Config File and pass
that path if the Settings dialog must persist changes. CLI overrides similarly
make the affected values non-editable for the session.

## `yes` or `no` behaves like text

labelme v7 parses YAML 1.2. Use `true` and `false` for booleans. This is a
format migration issue, not a Qt widget issue.

## Exact validation rejects a new label

Provide every allowed Label in the `--labels` source, or disable
`validate_label: exact`. Do not confuse the Label List with image-level Flags.

## GUI starts but settings do not persist

Check whether the session was started with inline `--config` or CLI overrides.
Those values are session-scoped. Use a writable Config File and confirm its
parent directory is writable.
