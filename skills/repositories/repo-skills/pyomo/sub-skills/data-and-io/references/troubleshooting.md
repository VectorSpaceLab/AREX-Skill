# Data and IO Troubleshooting

## Purpose

Read this when a file-backed Pyomo model fails to load, instantiate, or inspect.

## Common failures

### `create_instance()` complains about missing indices or sets

Symptoms:

- `KeyError`, `IndexError`, or a load-time schema mismatch.
- Parameters or sets appear to be missing data.

Likely causes:

- The input file does not match the model index structure.
- A namespace or section name is wrong.

Recovery:

- Verify the set dimensions and index names in the model.
- Start from the smallest tutorial-style data file.
- Add namespaces only when the file actually contains multiple data blocks.

### Spreadsheet loaders fail

Symptoms:

- Excel examples fail even though the core package imports.

Likely causes:

- `openpyxl`, `xlrd`, or another spreadsheet helper is missing.
- The workbook format does not match the reader.

Recovery:

- Install only the spreadsheet package that matches the input format.
- Confirm the workbook type before assuming a Pyomo bug.

### File path or working-directory problems

Symptoms:

- The loader cannot find a file that exists in the original repo.

Likely causes:

- The example depends on a checkout-relative path.
- The current working directory is wrong.

Recovery:

- Copy the data file into the current working directory or use an explicit path.
- Do not rely on original-repo relative paths in a distilled workflow.

## Next step

If the problem is actually solver execution, CLI parsing, or a model family that
needs transformations, move to the matching sub-skill.
