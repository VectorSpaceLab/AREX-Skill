# Sequential workflows

## 1. Set up one-table sequence metadata

Use PAR only when rows are grouped into multiple sequences. A timestamp alone is not enough; the metadata needs a sequence key.

```python
from sdv.metadata import Metadata

# data is one pandas DataFrame with repeated sequence ids.
metadata = Metadata.detect_from_dataframes({'events': data})
metadata.update_column('session_id', table_name='events', sdtype='id')
metadata.update_column('event_time', table_name='events', sdtype='datetime')
metadata.set_sequence_key('session_id', table_name='events')
metadata.set_sequence_index('event_time', table_name='events')
metadata.validate()
```

Before fitting, check context candidates:

```python
context_cols = ['region', 'plan_start_date']
violations = {
    col: data.groupby('session_id')[col].nunique(dropna=False).loc[lambda s: s > 1]
    for col in context_cols
}
violations = {col: series for col, series in violations.items() if not series.empty}
if violations:
    raise ValueError(f'Context columns are not constant per sequence: {violations}')
```

If a context column changes within a sequence, either remove it from `context_columns` or convert the data so it truly describes the whole sequence.

## 2. Fit PAR and sample new sequences

```python
from sdv.sequential import PARSynthesizer

fit_data = data.sort_values(['session_id', 'event_time']).reset_index(drop=True)

synthesizer = PARSynthesizer(
    metadata=metadata,
    context_columns=['region', 'plan_start_date'],
    epochs=1,        # increase after the smoke workflow succeeds
    sample_size=1,
    cuda=False,      # set True only when torch/CUDA is available and desired
    verbose=True,
)
synthesizer.fit(fit_data)

synthetic = synthesizer.sample(num_sequences=100)
fixed_length = synthesizer.sample(num_sequences=10, sequence_length=30)
```

Post-checks that catch common PAR mistakes:

```python
assert synthetic['session_id'].nunique() <= len(synthetic)
for col in ['region', 'plan_start_date']:
    assert synthetic.groupby('session_id')[col].nunique(dropna=False).le(1).all()
```

Use `sequence_length` when downstream code requires equal-length sequences. Leave it as `None` when the learned sequence-length distribution should be preserved.

## 3. Generate sequential columns for known context rows

Use `sample_sequential_columns` when the caller already knows one row of context per desired sequence. This is different from ordinary conditional sampling: PAR fills the time-varying/sequential columns while preserving the provided context values.

```python
known_context = pd.DataFrame({
    'session_id': ['NEW-001', 'NEW-002'],
    'region': ['west', 'east'],
    'plan_start_date': pd.to_datetime(['2024-01-01', '2024-02-01']),
})

scenario_sequences = synthesizer.sample_sequential_columns(
    context_columns=known_context,
    sequence_length=7,
)
```

Guidelines:

- Create the synthesizer with `context_columns=[...]`; otherwise `sample_sequential_columns` raises a sampling error.
- Supply one row per requested sequence.
- Include the sequence key column when you need stable output ids such as `NEW-001` and `NEW-002`.
- Keep datetime context values compatible with the metadata format and the dtype used during fitting.
- Validate that each output sequence has the requested length and that each context column remains constant per sequence key.

## 4. Reduce long sequential data before fitting

For very large or very long sequence tables, subset complete sequences before PAR fitting.

```python
import numpy as np
from sdv.utils import get_random_sequence_subset

np.random.seed(7)
subset = get_random_sequence_subset(
    data=fit_data,
    metadata=metadata,
    num_sequences=200,
    max_sequence_length=100,
    long_sequence_subsampling_method='first_rows',
)
subset = subset.sort_values(['session_id', 'event_time']).reset_index(drop=True)

assert subset['session_id'].nunique() <= 200
assert subset.groupby('session_id').size().le(100).all()
```

Choose the long-sequence method by task intent:

- `'first_rows'`: preserve the start of each selected sequence.
- `'last_rows'`: preserve the most recent/end rows.
- `'random'`: keep a random subset of rows while preserving their original order.

## 5. Use PAR-compatible constraints

Attach constraints before fitting and keep constraint scopes separated.

```python
from sdv.cag import FixedCombinations

synthesizer = PARSynthesizer(metadata, context_columns=['region'], epochs=1)
synthesizer.add_constraints([
    FixedCombinations(column_names=['region']),  # context-only example
])
synthesizer.fit(fit_data)
```

Compatibility rules:

- A constraint may cover context columns only, or non-context sequential columns only.
- A constraint may not mix context and non-context columns.
- Multiple constraints may not overlap on the same columns.
- Programmable constraints must be single-table compatible.

For custom constraint class design, use the constraints sub-skill first, then return here to attach and fit PAR.

## 6. Save and load a PAR synthesizer

```python
model_path = 'par_synthesizer.pkl'
synthesizer.save(model_path)

loaded = PARSynthesizer.load(model_path)
loaded_sample = loaded.sample(num_sequences=5, sequence_length=10)
```

Portability notes:

- Save after fitting when the loaded model must be immediately sampleable.
- Prefer `cuda=False` before fitting if the saved model must load on CPU-only machines.
- After loading, compare `loaded.get_info()` and `loaded.get_metadata().to_dict()` when debugging lifecycle or metadata drift.
