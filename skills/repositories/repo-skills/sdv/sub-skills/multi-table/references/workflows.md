# Multi-table workflows

Use these recipes after data and metadata are prepared. For basic loading and metadata detection, route to the data-preparation sub-skill first.

## 1. Build and validate a two-table fixture

```python
from sdv.metadata import Metadata

metadata = Metadata()
metadata.add_table('customers')
metadata.add_column('customer_id', table_name='customers', sdtype='id')
metadata.add_column('segment', table_name='customers', sdtype='categorical')
metadata.set_primary_key('customer_id', table_name='customers')

metadata.add_table('orders')
metadata.add_column('order_id', table_name='orders', sdtype='id')
metadata.add_column('customer_id', table_name='orders', sdtype='id')
metadata.add_column('amount', table_name='orders', sdtype='numerical')
metadata.set_primary_key('order_id', table_name='orders')
metadata.add_relationship(
    parent_table_name='customers',
    child_table_name='orders',
    parent_primary_key='customer_id',
    child_foreign_key='customer_id',
)

metadata.validate()
metadata.validate_data(data)
```

Validation should happen before any synthesizer is constructed. It catches missing tables, mismatched columns, duplicate primary keys, null/unknown foreign keys, and relationship graph problems.

## 2. Clean unknown foreign-key references

When child rows reference parent keys that do not exist, decide whether dropping those rows is acceptable.

```python
from sdv.utils import drop_unknown_references

try:
    metadata.validate_data(data)
except Exception:
    clean_data = drop_unknown_references(
        data=data,
        metadata=metadata,
        drop_missing_values=False,
        verbose=True,
    )
    metadata.validate_data(clean_data)
```

Use `drop_missing_values=True` only if rows with null foreign keys should also be removed. If the cleanup would remove an entire child table, inspect relationship direction and key sdtypes before continuing.

## 3. Fit and sample with `HMASynthesizer`

```python
from sdv.multi_table import HMASynthesizer

synthesizer = HMASynthesizer(metadata, verbose=True)
synthesizer.fit(clean_data)

same_scale = synthesizer.sample(scale=1.0)
smaller = synthesizer.sample(scale=0.5)
larger = synthesizer.sample(scale=1.5)
```

Post-checks:

```python
assert set(same_scale) == set(clean_data)
for table_name, table in same_scale.items():
    assert set(table.columns) == set(clean_data[table_name].columns)
metadata.validate_data(same_scale)
```

`scale` changes the expected size of generated tables while respecting relationships. It does not guarantee every table has exactly `len(real_table) * scale` rows.

## 4. Customize one table before fitting

HMA uses per-table single-table modeling under the hood. Inspect and set table parameters before fit when the defaults need tuning.

```python
synthesizer = HMASynthesizer(metadata)
params = synthesizer.get_table_parameters('orders')
params['default_distribution'] = 'gamma'
synthesizer.set_table_parameters('orders', params)
synthesizer.fit(clean_data)
```

For transformer changes:

```python
from rdt.transformers import FloatFormatter

synthesizer.auto_assign_transformers(clean_data)
transformers = synthesizer.get_transformers('orders')
transformers['amount'] = FloatFormatter(missing_value_replacement='mean')
synthesizer.update_transformers('orders', {'amount': transformers['amount']})
synthesizer.fit(clean_data)
```

Update transformers and table parameters before fitting. If you change them after fit, refit before sampling.

## 5. Attach multi-table constraints

Design constraint objects with the constraints sub-skill, then attach them here before fitting.

```python
from sdv.cag import FixedCombinations, Inequality
from sdv.multi_table import HMASynthesizer

constraints = [
    FixedCombinations(column_names=['country', 'city'], table_name='customers'),
    Inequality('min_amount', 'max_amount', table_name='orders'),
]

synthesizer = HMASynthesizer(metadata)
synthesizer.add_constraints(constraints)
synthesizer.fit(clean_data)
synthetic = synthesizer.sample(scale=1.0)
synthesizer.validate_constraints(synthetic)
```

Per-table constraints should name the target table. True cross-table logic belongs in a dictionary-style programmable constraint.

## 6. Save/load and reproduce sampling

```python
model_path = 'hma_synthesizer.pkl'
synthesizer.save(model_path)
loaded = HMASynthesizer.load(model_path)
loaded_sample = loaded.sample(scale=1.0)
```

Use `reset_sampling` when you need to reproduce the post-fit sample sequence:

```python
first = synthesizer.sample()
second = synthesizer.sample()
synthesizer.reset_sampling()
repeat_first = synthesizer.sample()
repeat_second = synthesizer.sample()
```

Sample equality depends on metadata, model state, random state, and dependency versions; use this as a repeatability tool, not a cross-version guarantee.

## 7. Multi-table DayZ parameter files

```python
from sdv.multi_table import DayZSynthesizer

parameters = DayZSynthesizer.create_parameters(
    data=clean_data,
    metadata=metadata,
    filepath='multi_table_dayz_parameters.json',
)
DayZSynthesizer.validate_parameters(metadata, parameters)
```

DayZ parameters include table-level and relationship-level settings. Edit cardinality bounds carefully:

```python
parameters['relationships'][0]['min_cardinality'] = 0
parameters['relationships'][0]['max_cardinality'] = 5
DayZSynthesizer.validate_parameters(metadata, parameters)
```

Do not instantiate `DayZSynthesizer(metadata)` for actual generation unless the runtime explicitly supports SDV Enterprise DayZ synthesis.

## 8. Evaluate generated relational data

After sampling, route to the evaluation sub-skill:

```python
from sdv.evaluation import evaluate_quality, run_diagnostic

quality = evaluate_quality(clean_data, synthetic, metadata)
diagnostic = run_diagnostic(clean_data, synthetic, metadata)
```

Keep fitting/sampling concerns in this sub-skill and metric/plot interpretation in the evaluation sub-skill.
