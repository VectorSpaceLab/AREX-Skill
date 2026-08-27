# Repo Provenance

- Source project: Lightning / PyTorch Lightning
- Source commit:   `fe6b1cc4e80ae0396e2e404c16e6b6968ad5437e`
- Source branch: `master`
- Exact tag: `none`
- Package version from source: `2.6.2`
- Remote URL: https://github.com/Lightning-AI/pytorch-lightning
- Generated skill id: `lightning`
- Generated from dirty checkout: yes

## Dirty State Summary

The checkout contained newly generated DisCo artifacts during integration. Relevant source evidence files were otherwise treated as read-only.

```text
  ?? skills/
```

## Evidence Paths

- `README.md`
- `setup.py`
- `pyproject.toml`
- `requirements.txt`
- `requirements/`
- `src/lightning/`
- `src/lightning/pytorch/`
- `src/pytorch_lightning/`
- `src/lightning/fabric/`
- `src/lightning_fabric/`
- `docs/source-pytorch/`
- `examples/pytorch/`
- `examples/fabric/`
- `tests/tests_pytorch/`
- `tests/tests_fabric/`
- `tests/parity_fabric/`

## Inspection Notes

Live inspection verified the current source package `lightning==2.6.2` and imports for `lightning`, `lightning.pytorch`, and `lightning.fabric`. Legacy `pytorch_lightning` compatibility was inspected as a compatibility surface; exact published compatibility package versions can lag the source version. CPU Torch was used for safe API/signature inspection, so this skill does not claim GPU, TPU, DeepSpeed, TensorRT, or distributed runtime validation.
