# Repository provenance

## Current checkout

- Repository: `tensorflow/privacy`
- Branch: `master`
- Commit: `e5d2dea72322d055887e7961dc44205da0540c8c`
- Remote: `tensorflow/privacy`

## Inspection environment

- Environment form: isolated private Python environment; its local path is intentionally not published
- Python: 3.11
- Verified runtime: CPU-only TensorFlow 2.15 stack plus the repo's requirements

## Evidence sources used

- `README.md`
- `requirements.txt`
- `setup.py`
- `setup_empirical.py`
- `g3doc/guide/`
- `tutorials/`
- `tensorflow_privacy/privacy/analysis/`
- `tensorflow_privacy/privacy/dp_query/`
- `tensorflow_privacy/privacy/privacy_tests/`
- `tensorflow_privacy/privacy/fast_gradient_clipping/`
- `tensorflow_privacy/privacy/sparsity_preserving_noise/`

## Evidence intentionally excluded from the minimum scope

- `research/`
- maintainer packaging and docs-build helpers
- notebook and codelab executions that would require external downloads or extra compatibility recovery
- optional `tensorflow_models` / `tensorflow_hub` / TFDS-linked fast-clipping paths

## Construction constraints

- Generate a repo-specific operating skill only.
- Do not import the generated skill at the end.
- Keep verification CPU-only.
- Keep unresolved optional dependency paths explicit instead of forcing them into the minimum verified scope.
