# Constraints API reference

## Import surfaces

```python
from sdv.cag import (
    FixedCombinations,
    FixedIncrements,
    Inequality,
    OneHotEncoding,
    ProgrammableConstraint,
    Range,
    SingleTableProgrammableConstraint,
)
from sdv.utils import load_constraints
```

Use `sdv.cag` for current synthesizer workflows. Legacy tabular constraints live in `sdv.constraints` and include `create_custom_constraint_class`, `FixedCombinations`, `Inequality`, `ScalarInequality`, `Range`, `ScalarRange`, `FixedIncrements`, `OneHotEncoding`, `Unique`, `Positive`, and `Negative`. Legacy `Constraint.to_dict()` / `Constraint.from_dict()` use the `constraint_class` and `constraint_parameters` keys.

## Current CAG vs legacy tabular constraints

| Family | Main use | Data shape | Serialization shape | Notes |
| --- | --- | --- | --- | --- |
| Current CAG (`sdv.cag`) | `synthesizer.add_constraints([...])`, `get_constraints`, `load_constraints`, `validate_constraints` | Single-table synthesizers use a `DataFrame`; multi-table synthesizers use `dict[str, DataFrame]`; programmable constraints may choose either interface | `{"class_name": "Inequality", "parameters": {...}}` | Preferred for new SDV workflows. Built-ins accept optional `table_name` when one table must be selected. |
| Legacy tabular (`sdv.constraints`) | Older tabular/data-processor code and legacy constraint dictionaries | Single `DataFrame` | `{"constraint_class": "sdv.constraints.tabular.FixedCombinations", "constraint_parameters": {...}}` | Do not pass old dictionary-style constraints to current `add_constraints`; they are ignored with a warning. Scalar-style constraints are deprecated in favor of synthesizer min/max handling where possible. |

## Built-in CAG constructors

| Constraint | Constructor | Valid columns | Effect |
| --- | --- | --- | --- |
| `FixedCombinations` | `FixedCombinations(column_names, table_name=None)` | At least two boolean or categorical columns | Learns allowed value combinations and preserves them. |
| `Inequality` | `Inequality(low_column_name, high_column_name, strict_boundaries=False, table_name=None)` | Two numerical or two datetime columns with the same sdtype | Enforces `high >= low` by default; `strict_boundaries=True` enforces `high > low`. |
| `Range` | `Range(low_column_name, middle_column_name, high_column_name, strict_boundaries=True, table_name=None)` | Three numerical or three datetime columns with the same sdtype | Enforces the middle column between low and high; default is strict. |
| `FixedIncrements` | `FixedIncrements(column_name, increment_value, table_name=None)` | One numerical column | Enforces values divisible by a positive whole-number increment. |
| `OneHotEncoding` | `OneHotEncoding(column_names, table_name=None, learning_strategy='one_hot')` | One-hot columns; numeric, boolean, or categorical metadata can be supported | Enforces exactly one active column per row. `learning_strategy='categorical'` internally collapses the group into one categorical column. |

CAG constraints cannot transform primary-key columns. Some also reject columns that participate in column relationships. For multi-table synthesizers, single-table constraints must have `table_name`.

## Legacy tabular constructors

| Constraint | Constructor | Notes |
| --- | --- | --- |
| `FixedCombinations` | `FixedCombinations(column_names)` | At least two columns; metadata sdtypes should be boolean/categorical. |
| `Inequality` | `Inequality(low_column_name, high_column_name, strict_boundaries=False)` | Numerical or datetime columns with matching sdtypes. |
| `Range` | `Range(low_column_name, middle_column_name, high_column_name, strict_boundaries=True)` | Numerical or datetime columns with matching sdtypes. |
| `FixedIncrements` | `FixedIncrements(column_name, increment_value)` | Positive whole-number increment. |
| `OneHotEncoding` | `OneHotEncoding(column_names)` | Rows must contain one 1 and remaining 0 values. |
| `Unique` | `Unique(column_names)` | Keeps only the first occurrence of each value combination during validity filtering. |
| `ScalarInequality` | `ScalarInequality(column_name, relation, value)` | Deprecated scalar comparison; `relation` is one of `>`, `>=`, `<`, `<=`. |
| `ScalarRange` | `ScalarRange(column_name, low_value, high_value, strict_boundaries=True)` | Deprecated scalar range. |
| `Positive` / `Negative` | `Positive(column_name, strict_boundaries=False)`, `Negative(column_name, strict_boundaries=False)` | Legacy scalar wrappers around zero. |

## Custom legacy constraint factory

```python
from sdv.constraints import create_custom_constraint_class

CustomConstraint = create_custom_constraint_class(
    is_valid_fn,
    transform_fn=None,
    reverse_transform_fn=None,
)
constraint = CustomConstraint(column_names=['col_a', 'col_b'], **kwargs)
```

Function contracts:

- `is_valid_fn(column_names, data, **kwargs) -> pandas.Series` with exactly one boolean per input row.
- `transform_fn(column_names, data, **kwargs) -> pandas.DataFrame` and `reverse_transform_fn(column_names, data, **kwargs) -> pandas.DataFrame` must be provided together or omitted together.
- Transform and reverse-transform functions must preserve row count. Return copies or new frames instead of mutating caller-owned data unexpectedly.

## Programmable constraints

Subclass `ProgrammableConstraint` for current CAG-compatible custom logic. Save every `__init__` parameter as an attribute with the same name or a matching private name so `get_constraint_dict()` can serialize it.

Required methods for a useful programmable constraint:

- `transform(data)`
- `get_updated_metadata(metadata)`
- `reverse_transform(transformed_data)`
- `is_valid(synthetic_data)`

Optional methods:

- `validate(metadata)` for table, column, sdtype, or relationship checks.
- `validate_input_data(data)` for real-data checks before fit.
- `fit(data, metadata)` for learned state.
- `fix_data(synthetic_data)` for DayZ-style post-processing.

Interface choices:

- `ProgrammableConstraint` normally receives and returns `dict[str, DataFrame]`. Set `_is_single_table = True` when the constraint targets one table but you still want the dictionary interface.
- `SingleTableProgrammableConstraint` is a backward-compatible DataFrame interface. In multi-table metadata it must expose `table_name`, or validation raises an error.

`is_valid` must return `dict[str, pandas.Series]` for the dictionary interface, with all unaffected tables mapped to all-True series, or a single `pandas.Series` for `SingleTableProgrammableConstraint`.

## Synthesizer methods

| Method | Contract | Important behavior |
| --- | --- | --- |
| `add_constraints(constraints)` | `constraints` must be a list of current CAG objects or programmable constraints. | Adding after fit emits a refit warning; refit before sampling. Single-table synthesizers reject multi-table-only constraints. |
| `get_constraints(filepath=None)` | Returns applied constraints when `filepath` is `None`; otherwise writes a JSON list. | Refuses to overwrite an existing file. JSON entries use `class_name` and `parameters`. |
| `set_constraints(filepath)` | Deprecated loader attached to synthesizers. | Fails if constraints already exist. Prefer `load_constraints(filepath)` plus `add_constraints`. |
| `validate_constraints(synthetic_data)` | Checks sampled data against applied constraints. | For multi-table synthesizers, pass `dict[str, DataFrame]`; errors name the table and row indices. |

Sequential `PARSynthesizer` has extra limits: built-in constraints cannot overlap on columns, and a constraint must cover either all context columns or all non-context columns, not a mix.

## Current constraints JSON shape

```json
[
  {
    "class_name": "FixedCombinations",
    "parameters": {
      "column_names": ["country", "city"],
      "table_name": "guests"
    }
  },
  {
    "class_name": "Inequality",
    "parameters": {
      "low_column_name": "checkin_date",
      "high_column_name": "checkout_date",
      "strict_boundaries": false,
      "table_name": "sessions"
    }
  }
]
```

`load_constraints(filepath)` loads known classes from `sdv.cag` and, when present, `sdv.cag.sandbox`. Unknown classes warn and are skipped rather than stopping the entire load.
