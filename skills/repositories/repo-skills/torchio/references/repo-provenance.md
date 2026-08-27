# Repo Provenance

## Source Snapshot

- Repository: TorchIO
- Source URL: https://github.com/TorchIO-project/torchio
- Branch: `main`
- Commit: `7b20416071b6cf69aa8e07dc1fda907fa379bb60`
- Exact tag: none detected at generation time
- Package version: `2.0.0a1`
- Working tree state: dirty because DisCo generated `skills/` artifacts in this checkout

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `src/torchio/`
- `docs/get-started/`
- `docs/concepts/`
- `docs/how-to/`
- `docs/tutorials/`
- `docs/reference/`
- `docs/examples/*.py`
- `tests/test_image.py`, `tests/test_subject.py`, `tests/test_points.py`, `tests/test_bboxes.py`, `tests/test_affine.py`
- `tests/test_transforms_base.py`, `tests/test_compose.py`, `tests/test_one_of.py`, `tests/test_some_of.py`, `tests/test_inverse.py`, `tests/test_parameter_range.py`
- `tests/test_patches.py`, `tests/test_queue.py`, `tests/test_batch.py`, `tests/test_tensordict.py`
- `tests/test_cli.py`, `tests/test_backends.py`, `tests/test_remote_loading.py`, `tests/test_remote_zarr.py`

## Refresh Notes

Refresh this skill when TorchIO changes public transform names, constructor signatures, CLI subcommands, patch sampler/aggregator behavior, optional extras, or the package version in `pyproject.toml`.
