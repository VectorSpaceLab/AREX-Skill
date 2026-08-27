# Troubleshooting

## Fast recovery order

1. Run `python -m fate.components component --help`.
2. Run `python -m fate.components component list --save <file>`.
3. Run `python -m fate.components component desc --name psi --save <file>`.
4. Run `python -m fate.components component task-schema --save <file>`.
5. Only then move on to stage-specific `artifact-type` checks.

## Missing `pkg_resources` or `setuptools`

### Symptom
- `import pkg_resources` fails.
- `component list` or `component desc` crashes before any catalog output appears.

### Why it happens
- The runtime loader imports `pkg_resources` to scan third-party entry points.
- If `setuptools` is missing, discovery cannot even build the catalog.

### Recovery
- Repair the Python environment so `setuptools` is installed and importable.
- Re-run the safe helper script after the environment is repaired.
- If the environment is shared, prefer a private inspection prefix instead of mutating the shared one.

## Unknown component name

### Symptom
- `RuntimeError: could not find registered cpn named ...`
- `Component ... does not exist.`

### Why it happens
- The runtime uses exact component ids, not filenames or display labels.
- Built-ins are loaded before third-party entry points, so a typo will not fall back to a fuzzy match.

### Recovery
- Run `component list` and copy the exact id from `buildin` or `thirdparty`.
- If the component should come from a plugin, verify that the plugin actually exposes `fate.ext.component_desc`.

## Unsupported stage

### Symptom
- `stage '<name>' not supported for component '<component>'`.

### Why it happens
- The component only declares some stage methods.
- A default-stage component does not automatically support `train`, `predict`, or `cross_validation`.

### Recovery
- Check `component desc --name <component>` for the component definition.
- Check `component artifact-type --name <component> --role <role> --stage <stage>` for the active I/O view.
- Switch to one of the stage names returned in the error message.

## Entry-point load failures

### Symptom
- `register cpn from entrypoint(named=..., module=...) failed: ...` warnings appear in the log.
- A third-party component is missing from `thirdparty` even though the package is installed.

### Why it happens
- The entry-point target imports a broken dependency, has an import-time exception, or returns a component with an unexpected name.
- The loader logs the failure and continues so that one broken plugin does not hide the whole built-in catalog.

### Recovery
- Fix the plugin import or dependency issue.
- Re-run `component list` to confirm the plugin now appears.
- If the plugin is optional, ignore it and use the built-ins.

## Schema or descriptor confusion

### Symptom
- A user thinks `task-schema` should show component artifact names.
- A user thinks `desc` should validate a live task config.
- A user expects `artifact-type` to show the full merged descriptor.

### Why it happens
- These commands answer different questions:
  - `list` answers “which components exist?”
  - `desc` answers “what is the merged component descriptor?”
  - `task-schema` answers “what fields does `TaskConfigSpec` accept?”
  - `artifact-type` answers “what I/O is active for this role and stage?”

### Recovery
- Use the matching command for the question.
- When in doubt, compare `desc` and `artifact-type` side by side.

## URI and artifact mismatch

### Symptom
- `load as input artifact(...) error`
- `load as output artifact(...) error`
- Errors about template URIs or type names.

### Why it happens
- The task config does not match the component descriptor.
- Multi-output components require template URIs containing `{index}`.
- Singleton outputs reject template URIs.

### Recovery
- Check the component’s `desc` output for the exact input/output names.
- Check `artifact-type` for the active role/stage artifacts.
- Confirm the `type_name` when you need a specific artifact implementation.

## When to stop and inspect instead of executing

- If you only need the CLI surface or descriptor shape, stay with `help`, `list`, `desc`, `artifact-type`, and `task-schema`.
- Do not use `execute` as a smoke check unless you already have a live config, supported backend, and a place to send the output meta file.
