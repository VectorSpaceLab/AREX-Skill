---
name: data-interfaces
description: "Validate, convert, load, and serialize sktime data containers and
  tiny datasets without relying on source checkout files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Data Interfaces

Use this sub-skill when a task is about `sktime` data containers, scitypes,
mtypes, validation/conversion, onboard or downloaded datasets, and time-series
file formats.

## Route here

- Decide whether data is `Series`, `Panel`, `Hierarchical`, or `Table`.
- Validate or convert pandas/numpy containers with `check_is_mtype` and `convert_to`.
- Load onboard datasets such as airline, ArrowHead, BasicMotions, or Tecator.
- Explain downloaded dataset surfaces and cache/network requirements.
- Read or write `.ts`, `.tsf`, ARFF, UCR TSV, and long-table time-series files.

## Route away

Estimator fitting and scoring route to the owning workflow sub-skill after data
is valid.

## References and helper

- [Data formats](references/data-formats.md) for scitypes, mtypes, validation,
  conversion, and panel/hierarchical layout rules.
- [Dataset and file I/O](references/dataset-io.md) for onboard loaders,
  downloaded datasets, and file serialization.
- [Troubleshooting](references/troubleshooting.md) for validation messages,
  MultiIndex issues, loader/cache failures, and missing labels.
- Run [scripts/check_data_format.py](scripts/check_data_format.py) and
  [scripts/tsfile_roundtrip.py](scripts/tsfile_roundtrip.py) for offline checks.
