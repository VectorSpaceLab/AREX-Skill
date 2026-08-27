# Single-Table Workflows

Use these recipes with a prepared pandas `DataFrame` named `real_data` and a valid single-table `metadata` object.

## 1. Choose, Fit, and Sample

Start with `GaussianCopulaSynthesizer` unless the task specifically asks for CTGAN/TVAE/CopulaGAN or neural-model behavior.

```python
from sdv.single_table import GaussianCopulaSynthesizer

synthesizer = GaussianCopulaSynthesizer(
    metadata,
    enforce_min_max_values=True,
    enforce_rounding=True,
)
synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(num_rows=500)
```

Model-specific constructor choices:

```python
from sdv.single_table import CTGANSynthesizer, TVAESynthesizer, CopulaGANSynthesizer

ctgan = CTGANSynthesizer(metadata, epochs=100, batch_size=500, enable_gpu=True)
tvae = TVAESynthesizer(metadata, epochs=100, batch_size=500, enable_gpu=True)
copulagan = CopulaGANSynthesizer(
    metadata,
    epochs=100,
    numerical_distributions={'amount': 'gamma'},
    default_distribution='beta',
    enable_gpu=True,
)
```

Deep models can take much longer than GaussianCopula. For a quick smoke run, lower `epochs`; for portable CPU-only artifacts, set `enable_gpu=False` before fitting.

## 2. Preprocess Then Fit Processed Data

Use this only when the same synthesizer instance owns the preprocessing.

```python
synthesizer = GaussianCopulaSynthesizer(metadata)
processed = synthesizer.preprocess(real_data.copy())

# Inspect or persist the processed table if needed. Do not change column meaning.
synthesizer.fit_processed_data(processed)
synthetic_data = synthesizer.sample(num_rows=100)
```

Do not pass raw data to `fit_processed_data`; call `fit(real_data)` for the normal end-to-end path.

## 3. Conditional Sampling

Use `Condition` for repeated identical conditions.

```python
from sdv.sampling import Condition

conditions = [
    Condition(column_values={'segment': 'premium'}, num_rows=25),
    Condition(column_values={'segment': 'standard'}, num_rows=25),
]
synthetic = synthesizer.sample_from_conditions(
    conditions,
    max_tries_per_batch=200,
    batch_size=100,
)
```

Use `DataFrameCondition` when each requested row can have different values.

```python
import pandas as pd
from sdv.sampling import DataFrameCondition

condition_rows = pd.DataFrame({
    'segment': ['premium', 'standard', 'premium'],
    'region': ['west', 'east', 'south'],
})
conditions = [DataFrameCondition(condition_rows)]
synthetic = synthesizer.sample_from_conditions(conditions, max_tries_per_batch=300)
```

Use `sample_remaining_columns` when you already have partial rows and need SDV to complete the rest.

```python
known_columns = pd.DataFrame({
    'segment': ['premium', 'standard'],
    'region': ['west', 'east'],
})
completed = synthesizer.sample_remaining_columns(
    known_columns,
    max_tries_per_batch=300,
    batch_size=100,
)
```

Rules and trade-offs:

- Condition columns must be original data/metadata columns and cannot be the primary key.
- GaussianCopula can pass conditions to its underlying model. CTGAN, TVAE, and CopulaGAN expose the same public methods but rely on SDV filtering/reject sampling when the underlying model cannot honor conditions directly.
- Rare, impossible, or constraint-incompatible conditions may return fewer rows, warn, or fail. Increase `max_tries_per_batch` and `batch_size` only after checking that the requested values are plausible.

## 4. Save and Load a Synthesizer

```python
from sdv.single_table import GaussianCopulaSynthesizer

synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_data)
synthesizer.save('single_table_synthesizer.pkl')

loaded = GaussianCopulaSynthesizer.load('single_table_synthesizer.pkl')
synthetic = loaded.sample(num_rows=100)
```

For deep models that may be loaded on a CPU-only machine later, fit with `enable_gpu=False` before saving:

```python
portable_ctgan = CTGANSynthesizer(metadata, epochs=100, enable_gpu=False)
portable_ctgan.fit(real_data)
portable_ctgan.save('portable_ctgan.pkl')
```

If using a class-specific `load`, use the class that created the file. Saving before fitting is allowed but warns; a loaded unfitted synthesizer still cannot sample until fitted.

## 5. Add Constraints to a Single-Table Model

Use the constraints sub-skill to design the constraint object, then attach it here before fitting.

```python
from sdv.constraints import FixedCombinations, Inequality
from sdv.single_table import GaussianCopulaSynthesizer

constraints = [
    FixedCombinations(column_names=['country', 'state']),
    Inequality(low_column_name='start_date', high_column_name='end_date'),
]

synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.add_constraints(constraints)
synthesizer.fit(real_data)
synthetic = synthesizer.sample(num_rows=200)
synthesizer.validate_constraints(synthetic)
```

Operational notes:

- Add constraints before `fit` whenever possible.
- `get_metadata(version='modified')` shows metadata after constraints update it.
- `get_constraints()` returns constraint objects; `get_constraints(filepath='constraints.json')` writes JSON only if the target file does not already exist.
- `set_constraints(filepath)` is deprecated and fails if constraints have already been applied. Prefer explicit constraint constructors plus `add_constraints`.

## 6. Customize Transformers

Use transformer customization when defaults hurt quality, speed, or anonymization behavior.

```python
from rdt.transformers import GaussianNormalizer, OneHotEncoder
from sdv.single_table import GaussianCopulaSynthesizer

synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.auto_assign_transformers(real_data)
current = synthesizer.get_transformers()

synthesizer.update_transformers({
    'amount': GaussianNormalizer(),
    'category': OneHotEncoder(),
})
synthesizer.fit(real_data)
```

Transformer rules:

- Call `auto_assign_transformers` or `fit` before `get_transformers`; otherwise no mapping exists.
- Do not pass a transformer that has already been fitted on data.
- Key columns require generator-style transformers; ordinary formatters for keys raise `SynthesizerInputError`.
- Updating after a model was already fitted emits a refit warning; call `fit` again before relying on the change.
- For CTGAN/TVAE/CopulaGAN, replacing default categorical or boolean handling can affect quality. For GaussianCopula, one-hot encoding categorical columns can slow preprocessing/modeling.

## 7. Inspect Parameters, Metadata, Distributions, and Losses

```python
info = synthesizer.get_info()
params = synthesizer.get_parameters()
original_metadata = synthesizer.get_metadata(version='original')
modified_metadata = synthesizer.get_metadata(version='modified')
```

For GaussianCopula or CopulaGAN after fitting:

```python
learned = synthesizer.get_learned_distributions()
```

For CTGAN, TVAE, or CopulaGAN after fitting:

```python
loss_values = synthesizer.get_loss_values()
loss_fig = synthesizer.get_loss_values_plot(title='Training loss')
```

Loss and learned-distribution methods fail before `fit`.

## 8. Deep Model GPU Usage

```python
ctgan = CTGANSynthesizer(metadata, epochs=300, enable_gpu=True)
ctgan.fit(real_data)
```

Guidelines:

- Use `enable_gpu=True` only when torch can see a compatible GPU; otherwise SDV/ctgan may fall back or error depending on the environment.
- Use `enable_gpu=False` for reproducible CPU-only examples, small data, or saved models that must be portable to CPU-only machines.
- Do not use the deprecated `cuda` argument in new code. Replace `cuda=False` with `enable_gpu=False`; remove `cuda` if `enable_gpu` is already present.

## 9. DayZ Parameters

In community SDV, only parameter creation and validation are public.

```python
from sdv.single_table import DayZSynthesizer

parameters = DayZSynthesizer.create_parameters(
    data=real_data,
    metadata=metadata,
    filepath='dayz_parameters.json',
)
DayZSynthesizer.validate_parameters(metadata, parameters)
```

Do not instantiate `DayZSynthesizer(metadata)` unless the runtime has SDV Enterprise support for actual DayZ synthesis.

## 10. Legacy `SingleTablePreset`

```python
from sdv.lite import SingleTablePreset

preset = SingleTablePreset(metadata, name='FAST_ML')
preset.fit(real_data)
synthetic = preset.sample(num_rows=100)
```

Prefer the modern equivalent unless maintaining legacy code:

```python
synthesizer = GaussianCopulaSynthesizer(
    metadata,
    default_distribution='norm',
    enforce_rounding=False,
)
```
