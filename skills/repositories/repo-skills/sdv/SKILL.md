---
name: sdv
description: "Use the Synthetic Data Vault (SDV) Python package for tabular
  synthetic data preparation, constraints, synthesis, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV repo skill

Use this repo skill when a task involves the Synthetic Data Vault (SDV) package: preparing tabular data and metadata, defining constraints, generating synthetic data for single-table, multi-table, or sequential data, and evaluating or visualizing synthetic data quality.

## Install and smoke check

Install the public package in the task runtime:

```bash
python -m pip install sdv
# Optional Excel local I/O support:
python -m pip install "sdv[excel]"
```

Conda users can follow the public install route from the README:

```bash
conda install -c pytorch -c conda-forge sdv
```

Minimal import check:

```bash
python - <<'PY'
import sdv
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer
print(sdv.__version__)
print(Metadata, GaussianCopulaSynthesizer)
PY
```

For a broader environment diagnostic, run [scripts/check_import.py](scripts/check_import.py) from this skill directory. Use `--require-dot` when metadata file rendering is required and `--check-cuda` or `--require-cuda` when deep-model GPU support matters.

## Route by task

| User task | Read |
| --- | --- |
| Load demo data, read/write local CSV or Excel files, detect/edit/validate metadata, visualize metadata, clean foreign-key references, inspect logs, or subset sequential rows before modeling. | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Add or debug built-in CAG constraints, legacy tabular constraints, custom constraints, programmable constraints, constraint JSON files, or synthesizer constraint methods. | [constraints](sub-skills/constraints/SKILL.md) |
| Fit/sample one pandas DataFrame with GaussianCopula, CTGAN, TVAE, CopulaGAN, single-table DayZ parameters, or legacy SingleTablePreset. | [single-table](sub-skills/single-table/SKILL.md) |
| Fit/sample relational datasets represented as `dict[str, pandas.DataFrame]` with HMA or multi-table DayZ parameters. | [multi-table](sub-skills/multi-table/SKILL.md) |
| Model one sequence-keyed table with PAR, sequence keys/indexes, context columns, or `sample_sequential_columns`. | [sequential](sub-skills/sequential/SKILL.md) |
| Run quality reports, diagnostic reports, single/multi-table plots, or cardinality plots after synthetic data is generated. | [evaluation](sub-skills/evaluation/SKILL.md) |

## Important operating boundaries

- SDV is primarily a Python API workflow in this snapshot. Do not assume an `sdv` command-line interface is usable unless the target installed package separately verifies it.
- Prepare and validate `Metadata` before choosing a synthesizer; most confusing fit/sample errors come from mismatched sdtypes, keys, or relationships.
- Add constraints before fitting whenever possible; if constraints or transformers are changed after fit, refit before sampling.
- Use `enable_gpu=False` for portable CPU-only single-table deep-model artifacts and `cuda=False` for portable PAR artifacts. Use GPU only after torch/CUDA is verified in the task runtime.
- SDV quality reports measure statistical similarity and validity, not privacy guarantees. Add separate privacy or downstream-utility checks when requested.
- Keep generated data, model pickle files, metadata JSON, plots, and logs outside the skill directory.

## Shared references

- [Repository provenance](references/repo-provenance.md): source commit, version, evidence paths, and refresh checks.
- [Root API reference](references/api-reference.md): public module map, dependency notes, and top-level workflow surfaces.
- [Root workflows](references/workflows.md): end-to-end routing patterns that combine multiple sub-skills.
- [Root troubleshooting](references/troubleshooting.md): cross-cutting installation, import, backend, and routing failures.
