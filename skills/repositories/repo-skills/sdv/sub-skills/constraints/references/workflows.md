# Constraint workflows

## Add built-in CAG constraints

1. Ensure metadata already defines the table and columns with compatible sdtypes.
2. Instantiate current `sdv.cag` objects.
3. Add constraints before fitting the synthesizer.
4. Fit and sample through the appropriate synthesis sub-skill.
5. Use `validate_constraints` when you need to check sampled rows.

```python
from sdv.cag import FixedCombinations, FixedIncrements, Inequality, OneHotEncoding, Range

constraints = [
    FixedCombinations(column_names=['country', 'city'], table_name='guests'),
    Inequality('checkin_date', 'checkout_date', table_name='sessions'),
    Range('min_price', 'price', 'max_price', strict_boundaries=False, table_name='rooms'),
    FixedIncrements('reward_points', increment_value=10, table_name='guests'),
    OneHotEncoding(['basic', 'premium', 'vip'], table_name='guests'),
]

synthesizer.add_constraints(constraints)
```

For a single-table synthesizer, omit `table_name` unless the metadata uses a named table and the constraint needs it for serialization clarity.

## Choose the right built-in

- Use `FixedCombinations` when only combinations seen in real data are valid, such as `(country, city)` or `(has_rewards, room_type)`.
- Use `Inequality` when one numerical or datetime column must be at least another.
- Use `Range` when a middle numerical or datetime column must stay between two bound columns.
- Use `FixedIncrements` for currency, points, quantities, or other positive whole-number multiples.
- Use `OneHotEncoding` when several indicator columns must have exactly one active value per row. Try `learning_strategy='categorical'` when the model should learn the group as one categorical feature.
- Use legacy `Unique` only for old tabular workflows that need first-occurrence validity filtering; for new data modeling, prefer metadata primary/alternate keys where appropriate.

## Create a legacy custom constraint class

Use this only for legacy tabular/data-processor style constraints or when translating older code. For current synthesizer workflows, prefer a programmable constraint.

```python
import pandas as pd
from sdv.constraints import create_custom_constraint_class

def is_nonnegative(column_names, data, minimum=0):
    column = column_names[0]
    return data[column].ge(minimum).fillna(True)

NonNegative = create_custom_constraint_class(is_nonnegative)
constraint = NonNegative(column_names=['amount'], minimum=0)
```

If you define transforms:

```python
def transform(column_names, data, **kwargs):
    data = data.copy()
    # update or replace columns, but keep the same number of rows
    return data

def reverse_transform(column_names, data, **kwargs):
    data = data.copy()
    # reconstruct original columns, preserving row count
    return data

Custom = create_custom_constraint_class(is_nonnegative, transform, reverse_transform)
```

Preflight every custom legacy function with a small `DataFrame`: `is_valid` must return a `pandas.Series` of length `len(data)`, while transform and reverse-transform must return DataFrames with the same row count.

## Create a current programmable constraint

Use `ProgrammableConstraint` for custom logic that should attach with `add_constraints`.

```python
import pandas as pd
from sdv.cag import ProgrammableConstraint

class IfFlagThenZero(ProgrammableConstraint):
    _is_single_table = True

    def __init__(self, flag_column, value_column, table_name=None):
        self.flag_column = flag_column
        self.value_column = value_column
        self.table_name = table_name

    def validate(self, metadata):
        table = self.table_name or next(iter(metadata.tables))
        columns = metadata.tables[table].columns
        assert columns[self.flag_column]['sdtype'] == 'boolean'
        assert columns[self.value_column]['sdtype'] == 'numerical'

    def transform(self, data):
        table = self.table_name or next(iter(data))
        data = {name: frame.copy() for name, frame in data.items()}
        typical_value = data[table][self.value_column].median()
        data[table][self.value_column] = data[table][self.value_column].mask(
            data[table][self.flag_column], typical_value
        )
        return data

    def reverse_transform(self, transformed_data):
        table = self.table_name or next(iter(transformed_data))
        transformed_data = {name: frame.copy() for name, frame in transformed_data.items()}
        transformed_data[table][self.value_column] = transformed_data[table][self.value_column].mask(
            transformed_data[table][self.flag_column], 0.0
        )
        return transformed_data

    def get_updated_metadata(self, metadata):
        return metadata

    def is_valid(self, synthetic_data):
        table = self.table_name or next(iter(synthetic_data))
        valid = {name: pd.Series(True, index=frame.index) for name, frame in synthetic_data.items()}
        true_flag = synthetic_data[table][self.flag_column]
        zero_value = synthetic_data[table][self.value_column].eq(0.0)
        valid[table] = (~true_flag) | (true_flag & zero_value)
        return valid
```

Attach it like a built-in: `synthesizer.add_constraints([IfFlagThenZero('has_fee', 'fee', table_name='guests')])`.

## Use `SingleTableProgrammableConstraint` only for DataFrame-style methods

Subclass `SingleTableProgrammableConstraint` when you specifically need methods to receive one `DataFrame` rather than a dictionary. If metadata has multiple tables, the class must set `self.table_name` in `__init__`; otherwise validation fails. Its `is_valid` returns one `pandas.Series`, not a dictionary.

## Save and load constraints JSON

Save applied current constraints:

```python
synthesizer.get_constraints('constraints.json')
```

The output path must not already exist. The JSON is a list of `class_name` and `parameters` objects.

Load and attach constraints:

```python
from sdv.utils import load_constraints

constraints = load_constraints('constraints.json')
if len(constraints) != expected_count:
    # inspect warnings and the JSON entries before continuing
    raise RuntimeError('Some constraints did not load')

synthesizer.add_constraints(constraints)
```

Prefer this over `synthesizer.set_constraints(filepath)`, which is deprecated and also refuses to run if constraints are already applied.

## Refitting after constraint changes

- Best path: create metadata, create synthesizer, call `add_constraints`, then fit.
- If constraints are added after fitting, SDV warns that they will not take effect until refit. Call `fit` again before sampling.
- If changing constraint definitions materially changes metadata columns, start from a fresh synthesizer when practical; otherwise inspect `get_metadata('modified')` before refitting.
- Do not mix old legacy dictionary constraints with current CAG objects in `add_constraints`; translate old entries to CAG objects first.

## Load a mixed JSON file with unknown classes

1. Check that each entry has exactly `class_name` and `parameters`.
2. Load with `load_constraints` while capturing warnings.
3. Compare loaded count to file count.
4. For each skipped unknown class, either replace it with a built-in CAG class, make the class importable from the expected CAG sandbox surface, or instantiate the custom programmable class directly in Python instead of JSON-only loading.
5. Add only the loaded, reviewed constraints to the synthesizer and refit.
