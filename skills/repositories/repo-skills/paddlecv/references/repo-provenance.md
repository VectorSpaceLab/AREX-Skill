# Repository provenance

- Schema: `disco.repo-provenance.v1`
- Repository: PaddlePaddle `models`
- Canonical skill id: `paddlecv`
- Commit: `95d3f5467de2f418290eb4097a4e3aadbdc94b6d`
- Branch: `release/2.4`
- Tag at HEAD: none
- Remote URL: `https://github.com/PaddlePaddle/models.git`
- Package version observed from live import: `0.1.0`
- Generated from a dirty checkout: yes; final verification state only has expected generated artifacts under `skills/`.

## Source-side dirty state observed during generation
- Earlier transient source-side files were cleaned before final verification: `paddlecv/ppcv/model_zoo/MODEL_ZOO` and `paddlecv/paddlecv.egg-info/`.
- Current source baseline changes outside generated `skills/` artifacts: none observed.
- Generated DisCo outputs under `skills/disco/paddlecv/` and `skills/tests/paddlecv/` are expected skill artifacts, not source baseline changes.

## Evidence paths used
- `README.md`
- `paddlecv/README.md`
- `paddlecv/docs/INSTALL.md`
- `paddlecv/docs/GETTING_STARTED.md`
- `paddlecv/docs/whl.md`
- `paddlecv/docs/custom_ops.md`
- `paddlecv/docs/how_to_add_new_op.md`
- `paddlecv/docs/system_design.md`
- `paddlecv/docs/config_anno.md`
- `paddlecv/configs/single_op/`
- `paddlecv/configs/system/`
- `paddlecv/configs/unittest/`
- `paddlecv/paddlecv.py`
- `paddlecv/ppcv/core/config.py`
- `paddlecv/ppcv/core/workspace.py`
- `paddlecv/ppcv/engine/pipeline.py`
- `paddlecv/ppcv/model_zoo/model_zoo.py`
- `paddlecv/ppcv/ops/base.py`
- `paddlecv/ppcv/ops/models/`
- `paddlecv/ppcv/ops/connector/`
- `paddlecv/ppcv/ops/output/`
- `paddlecv/ppcv/utils/download.py`
- `paddlecv/tests/`
- `paddlecv/custom_op/test_custom_detection.py`
- `paddlecv/tools/predict.py`
- `paddlecv/tools/check_name.py`
- `modelcenter/PP-OCRv3/APP/app.py`
- `modelcenter/PP-LCNet/APP/app.py`

## Staleness check guidance
- Rebuild or refresh this skill if the source commit changes, the catalog of task names changes, the public `PaddleCV` signature changes, or the package stops importing with the documented dependency set.
- The generated skill is self-contained; do not use the original checkout as a runtime dependency.
