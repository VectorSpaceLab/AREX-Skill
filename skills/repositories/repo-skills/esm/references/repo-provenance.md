# Repository Provenance

This skill was generated from the ESM / fair-esm source repository.

## Source Snapshot

- VCS: git
- Branch: `main`
- Commit: `2b369911bb5b4b0dda914521b9475cad1656b2ac`
- Exact tag: none detected
- Working tree state at generation: dirty because generated DisCo output was present under `skills/`
- Remote URL: https://github.com/facebookresearch/esm
- Package distribution: `fair-esm`
- Package version observed during inspection: `2.0.1`

## Evidence Paths

The generated skill used these repository-relative evidence paths:

- `setup.py`
- `pyproject.toml`
- `README.md`
- `environment.yml`
- `hubconf.py`
- `esm/`
- `scripts/extract.py`
- `scripts/fold.py`
- `scripts/download_weights.sh`
- `scripts/atlas/README.md`
- `examples/README.md`
- `examples/esm2_infer_fairscale_fsdp_cpu_offloading.py`
- `examples/contact_prediction.ipynb`
- `examples/sup_variant_prediction.ipynb`
- `examples/inverse_folding/README.md`
- `examples/inverse_folding/sample_sequences.py`
- `examples/inverse_folding/score_log_likelihoods.py`
- `examples/inverse_folding/data/`
- `examples/variant-prediction/README.md`
- `examples/variant-prediction/predict.py`
- `examples/variant-prediction/data/`
- `tests/test_alphabet.py`
- `tests/test_load_all.py`
- `tests/test_inverse_folding.py`
- `tests/test_notebooks.py`
- `tests/test_readme.py`

## Refresh Signals

Refresh this skill if the repository changes any of these surfaces:

- Public model loader names or signatures in `esm/pretrained.py`.
- Tokenization, batching, FASTA, or MSA behavior in `esm/data.py`.
- Console script flags or behavior in `scripts/extract.py` or `scripts/fold.py`.
- ESMFold API behavior under `esm/esmfold/v1/`.
- Inverse-folding coordinate/scoring behavior under `esm/inverse_folding/`.
- Variant prediction workflow semantics in `examples/variant-prediction/predict.py`.
- Installation or optional dependency guidance in `setup.py`, `environment.yml`, or `README.md`.
