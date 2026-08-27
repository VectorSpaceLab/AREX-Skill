---
name: data-and-io
description: "Guides Pyomo users through AbstractModel loading, DataPortal
  input, and file-backed model initialization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and IO

Use this sub-skill when the task begins with a data file, a spreadsheet, a
configuration file, or an `AbstractModel` that needs `create_instance()`.

## What this sub-skill covers

- `AbstractModel` and `create_instance()` workflows.
- `DataPortal` and file-backed model initialization.
- `.dat`, `.tab`, Excel, YAML, and JSON inputs.
- Tutorial-style data loading and model instantiation.

## What to route elsewhere

- Pure model construction without external data goes to `modeling-basics`.
- `pyomo solve`, `pyomo convert`, and config-template questions go to
  `solve-and-cli`.
- GDP, DAE, network, MPEC, and units go to `structured-modeling`.
- Solver/back-end or GUI dependency issues go to `solver-extensions`.

## Read these references

- `../../references/data-and-io.md` for verified file-loading patterns and data
  families.
- `../../references/cli-reference.md` when the same data file is passed through
  a Pyomo CLI command.
- `../../references/troubleshooting.md` when a load fails because of a missing
  package, a bad namespace, or a schema mismatch.

## Use this helper

- `../../scripts/check_import.py` for a quick import and metadata sanity check
  before debugging a data-loading issue.

## Typical workflow

1. Declare an `AbstractModel` with the sets and parameters the data will fill.
2. Map the data file structure to the model indices and domains.
3. Load the data with `create_instance()` or `DataPortal`.
4. Inspect the instantiated model with `pprint()`.
5. Only then connect the instance to a solver or transformation.

## Common request patterns

- "How do I load a `.dat` file into my model?"
- "How do I use namespaces with `DataPortal`?"
- "How do I read Excel or tabular inputs into Pyomo?"
- "Why does `create_instance()` complain about missing indices?"
- "How do I generate or read a JSON/YAML config for a Pyomo run?"

## Common failure modes

- A set dimension in the data does not match the model declaration.
- A parameter value is missing or appears under the wrong namespace.
- Spreadsheet helpers are unavailable because optional packages are missing.
- A file path is wrong, relative to the wrong working directory, or only valid
  inside the original checkout.

## Practical guidance

- Keep the initial data example as small as possible.
- Verify the schema before scaling to a large file.
- Prefer explicit namespaces and explicit indices when multiple data blocks are
  involved.
- Use the tutorial-style examples as a reference pattern, but do not depend on
  the original repository path at runtime.

## Examples of what belongs here

- `AbstractModel` plus one `.dat` file.
- `DataPortal` loading from a table or spreadsheet.
- A CLI invocation that loads model data from a config file.

## Examples of what does not belong here

- Solver selection and execution flags.
- DAE, GDP, network, or complementarity workflows.
- Optional solver or GUI backends that are unrelated to file loading.

## Related routes

- Move to `modeling-basics` when the data file is not the main problem.
- Move to `solve-and-cli` when the task is about CLI execution after data load.
- Move to `structured-modeling` when the model family is GDP, DAE, network,
  MPEC, or units.
