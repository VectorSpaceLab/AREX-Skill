# SDV root workflows

These root workflows combine sub-skills. When a task narrows to one area, move to the owning sub-skill for details.

## 1. Minimal single-table synthetic data workflow

```python
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.evaluation import evaluate_quality, run_diagnostic

metadata = Metadata.detect_from_dataframe(real_data, table_name='customers')
metadata.validate()
metadata.validate_table(real_data, table_name='customers')

synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(num_rows=500)

diagnostic = run_diagnostic(real_data, synthetic_data, metadata)
quality = evaluate_quality(real_data, synthetic_data, metadata)
```

Route deeper steps:

1. Prepare or fix metadata with [data-preparation](../sub-skills/data-preparation/SKILL.md).
2. Add business rules with [constraints](../sub-skills/constraints/SKILL.md) before fitting.
3. Choose and tune the model with [single-table](../sub-skills/single-table/SKILL.md).
4. Score results with [evaluation](../sub-skills/evaluation/SKILL.md).

## 2. Relational/multi-table workflow

```python
from sdv.metadata import Metadata
from sdv.multi_table import HMASynthesizer
from sdv.utils import drop_unknown_references
from sdv.evaluation import evaluate_quality

metadata = Metadata.detect_from_dataframes(real_tables)
metadata.validate()

try:
    metadata.validate_data(real_tables)
except Exception:
    real_tables = drop_unknown_references(real_tables, metadata)
    metadata.validate_data(real_tables)

synthesizer = HMASynthesizer(metadata)
synthesizer.fit(real_tables)
synthetic_tables = synthesizer.sample(scale=1.0)
metadata.validate_data(synthetic_tables)
quality = evaluate_quality(real_tables, synthetic_tables, metadata)
```

Use [multi-table](../sub-skills/multi-table/SKILL.md) when relationships, sample scale, HMA table parameters, or relational DayZ parameters are the main issue. Use [evaluation](../sub-skills/evaluation/SKILL.md) for cardinality plots and report interpretation.

## 3. Sequential workflow

```python
from sdv.metadata import Metadata
from sdv.sequential import PARSynthesizer

metadata = Metadata.detect_from_dataframes({'events': events})
metadata.update_column('session_id', table_name='events', sdtype='id')
metadata.update_column('event_time', table_name='events', sdtype='datetime')
metadata.set_sequence_key('session_id', table_name='events')
metadata.set_sequence_index('event_time', table_name='events')
metadata.validate_table(events, table_name='events')

fit_data = events.sort_values(['session_id', 'event_time']).reset_index(drop=True)
synthesizer = PARSynthesizer(metadata, context_columns=['region'], epochs=1, cuda=False)
synthesizer.fit(fit_data)
synthetic_events = synthesizer.sample(num_sequences=50)
```

Use [sequential](../sub-skills/sequential/SKILL.md) for sequence-specific metadata, context columns, `sample_sequential_columns`, and long-sequence subsetting.

## 4. Constraint-first workflow

When a user describes business rules before model choice:

1. Use [data-preparation](../sub-skills/data-preparation/SKILL.md) to ensure metadata names, sdtypes, and table names are valid.
2. Use [constraints](../sub-skills/constraints/SKILL.md) to choose CAG built-ins or programmable constraints.
3. Attach constraints to the target synthesizer before `fit`.
4. Fit/sample in the relevant synthesis sub-skill.
5. Run `synthesizer.validate_constraints(synthetic_data)` and then use [evaluation](../sub-skills/evaluation/SKILL.md) for broader reports.

Example:

```python
from sdv.cag import FixedCombinations, Inequality
from sdv.single_table import GaussianCopulaSynthesizer

constraints = [
    FixedCombinations(['country', 'city']),
    Inequality('start_date', 'end_date'),
]

synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.add_constraints(constraints)
synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(500)
synthesizer.validate_constraints(synthetic_data)
```

## 5. Environment and optional dependency workflow

Run the root diagnostic when import, Graphviz, or CUDA is part of the task:

```bash
python scripts/check_import.py
python scripts/check_import.py --require-dot
python scripts/check_import.py --check-cuda
```

Interpretation:

- Import failures: fix package installation before using any sub-skill.
- Graphviz missing: data/metadata workflows can still create graph objects, but rendering files with `metadata.visualize(..., output_filepath=...)` requires `dot`.
- CUDA missing: CPU workflows remain valid; set `enable_gpu=False` or `cuda=False` unless the task explicitly requires GPU-backed deep models.

## 6. When to avoid SDV for a request

Do not use this skill when:

- The task is generic pandas cleaning with no synthetic-data, metadata, or SDV requirement.
- The user needs privacy guarantees, fairness audits, or model utility proofs without synthetic data generation; SDV reports may be one input but are not sufficient.
- The data is image, text, audio, graph, or tensor data rather than tabular/sequential relational data.
- The user asks to modify SDV repository source code or release machinery; that is repository maintenance, not a package-operating workflow.
