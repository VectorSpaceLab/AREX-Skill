# Data and IO

## Purpose

Read this when a Pyomo task starts from an `AbstractModel`, a data file, a
spreadsheet, or a configuration file rather than from a hand-built concrete
model.

## What it covers

- `AbstractModel` and `create_instance()` workflows.
- `DataPortal` loading and file-backed initialization.
- `.dat`, `.tab`, Excel, YAML, and JSON inputs that feed Pyomo models or CLI
  templates.
- Introductory tutorial-style data workflows.

## Verified API facts

The following objects are importable from `pyomo.environ` in this checkout:

- `AbstractModel(*args, **kwds)`
- `DataPortal(*args, **kwds)`
- `Set`, `Param`, `RangeSet`, `Var`, `Constraint`, `Objective`

## Typical file-backed workflow

```python
import pyomo.environ as pyo

model = pyo.AbstractModel()
model.I = pyo.Set()
model.p = pyo.Param(model.I)
# ... additional declarations ...
instance = model.create_instance("data.dat")
instance.pprint()
```

## Common input families

- **AMPL-style `.dat` files**: the standard small data-file format in Pyomo
  tutorials and examples.
- **Table files (`.tab`)**: useful for compact tabular data.
- **Excel spreadsheets**: supported when spreadsheet helpers such as `openpyxl`
  or `xlrd` are available; some notebook/COM paths are platform-specific.
- **YAML/JSON configuration files**: often used by `pyomo solve` and
  `pyomo convert` to provide model, solver, and output settings.

## Practical guidance

- Keep file paths relative to the current working directory or make them fully
  explicit in the calling script.
- Use namespaces when one data file contains several logical data blocks.
- Verify set dimensionality and parameter domains early; many file-loading
  errors are really schema mismatches.
- Prefer small tutorial-style examples for understanding data shape before
  wiring a large production model.

## Common gotchas

- Missing `openpyxl`, `xlrd`, or spreadsheet helpers can make Excel examples
  fail even when the core package imports cleanly.
- A bad namespace, wrong set dimension, or missing index entry usually appears
  as a load-time error, not a solver error.
- If a file-backed workflow works only inside the original checkout, it has not
  been distilled enough for this skill.

## Related references

- Read `core-modeling.md` for the component classes used in file-backed model
  construction.
- Read `cli-reference.md` for `pyomo solve` and `pyomo convert` workflows that
  consume data files or config files.
- Read `troubleshooting.md` when file loading or spreadsheet helpers fail.
