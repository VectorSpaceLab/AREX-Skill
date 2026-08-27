# CLI and Project Ops Troubleshooting

## `pai` command not found

**Cause**: Console scripts are not on the active environment's PATH or PandasAI is
installed in a different Python environment.

**Fix**: Activate the intended environment, reinstall PandasAI if necessary, and
run `python -c "import pandasai"` to verify the import.

## `ModuleNotFoundError: click`

**Cause**: The CLI module imports Click, but Click is absent in the current
environment.

**Fix**:

```bash
pip install click
```

Then retry `pai --help`.

## Invalid API key format

**Symptom**: CLI prints `Invalid API key format`.

**Cause**: `pai login` expects a `PAI-` key with UUID-like hexadecimal groups.

**Fix**: Confirm the key format before calling login. Never paste real keys into
public prompts, test fixtures, or logs.

## `.env` written in the wrong place

**Cause**: The command was run from a directory whose parent contains a project
marker, so PandasAI discovered that parent as the project root.

**Fix**: Run from the intended app root, or inspect where `pyproject.toml`,
`setup.py`, or `requirements.txt` is discovered.

## Guided dataset creation is hard to automate

**Cause**: `pai dataset create` is interactive and prompts for values.

**Fix**: For automation, prefer programmatic `pai.create`. For CLI tests, use an
isolated Click runner or an explicit input stream with fake credentials.

## Existing dataset error

**Symptom**: `Dataset already exists`.

**Cause**: The target `datasets/<org>/<dataset>/schema.yaml` exists.

**Fix**: Use a new dataset path, remove the old test fixture, or load the
existing dataset instead of creating it.

## Full repo targets are too broad

**Cause**: Make targets such as full extension tests install many optional
packages.

**Fix**: Select focused unit or integration tests for the changed surface. Use
all-extension targets only for extension development or release validation.
