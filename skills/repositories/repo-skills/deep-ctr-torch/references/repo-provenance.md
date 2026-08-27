# Repo provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from the public DeepCTR-Torch repository and package metadata listed below. Use this file to decide whether the skill should be refreshed for a newer checkout or package version.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | `shenweichen/DeepCTR-Torch` |
| Public remote URL | `https://github.com/shenweichen/DeepCTR-Torch.git` |
| Branch | `master` |
| Commit | `9eccef78e5810c61d6a04ddc7d96279e3db9c970` |
| Exact tag | none detected |
| Distribution name | `deepctr-torch` |
| Package import | `deepctr_torch` |
| Package version | `0.3.0` |
| License | Apache-2.0 |

## Working tree state

The repository working tree became dirty during skill construction because generated skill and review artifacts were written under `skills/`. No source evidence files under `deepctr_torch/`, `docs/`, `examples/`, `tests/`, or package metadata were intentionally modified for extraction.

Dirty summary at generation time:

```text
?? skills/
```

## Evidence paths used

Source and package metadata:

- `setup.py`
- `deepctr_torch/__init__.py`
- `deepctr_torch/inputs.py`
- `deepctr_torch/callbacks.py`
- `deepctr_torch/utils.py`
- `deepctr_torch/models/*.py`
- `deepctr_torch/models/multitask/*.py`
- `deepctr_torch/layers/*.py`

Documentation:

- `README.md`
- `docs/source/Quick-Start.md`
- `docs/source/Examples.md`
- `docs/source/Features.md`
- `docs/source/FAQ.md`
- selected autosummary files in `docs/source/deepctr_torch.*.rst`

Examples and behavior evidence:

- `examples/run_classification_criteo.py`
- `examples/run_regression_movielens.py`
- `examples/run_multivalue_movielens.py`
- `examples/run_din.py`
- `examples/run_dien.py`
- `examples/run_multitask_learning.py`
- bundled sample data names from `examples/*.txt` were used only as evidence; generated scripts use inline data instead.

Tests and CI evidence:

- `tests/utils.py`
- `tests/utils_mtl.py`
- `tests/callbacks_test.py`
- `tests/layers/*.py`
- `tests/models/*.py`
- `tests/models/multitask/*.py`
- `tests/ci/*.sh`
- `.github/workflows/ci.yml`

## Refresh triggers

Refresh this skill when:

- `deepctr-torch` releases a version newer than `0.3.0` with changed constructor signatures or dependency metadata.
- `deepctr_torch.inputs`, `BaseModel.compile/fit/predict/evaluate`, callback behavior, DIN/DIEN, or multitask constructors change.
- The package adds console entry points, new model families, new supported losses/metrics, or changes optional dependency/backend behavior.
- Native examples/tests are renamed or their expected data-shape patterns change.
