# CLI/config troubleshooting

## `TypeError` or `AssertionError` while reading a config

- Check that the file is a Python module that exports `main_config` and
  `create_config`.
- For distributed launch paths, confirm that `system_config` exists when the
  CLI path expects it.
- Make sure the config module imports cleanly on its own before it is passed to
  `compile_config`.

## `Please indicate at least one argument.`

- `ding` was called without a mode and without the `-e/-p` predefined lookup.
- Re-run with an explicit mode or a valid config path.

## `platform_spec is not a valid json!`

- The `ditask` platform spec was quoted or formatted incorrectly.
- Reduce the spec to a tiny JSON payload and validate the syntax before using
  the cluster-specific shape.

## `not support registry name`

- The registry name passed to `ding -q` does not match one of the known
  registry families.
- Re-run with the exact family name or use the bundled smoke script to inspect
  the registry list first.

## Config compiles but launch still fails

- `compile_config` succeeded, but the env wrapper, policy type, or checkpoint
  path still may be wrong.
- Route to `serial-pipelines` or `env-integration` depending on whether the
  next failure is about training logic or env shape.
