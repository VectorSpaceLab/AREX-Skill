# Repository provenance

**Schema:** `disco.repo-provenance.v1`

- **Package:** StarDist
- **Package version inspected:** 0.9.2
- **Source commit:** `e80c6de700693bc228ed3c9ba1dc19c3785667ee`
- **Branch:** `main`
- **Source state / dirty state:** tracked package source was clean at the inspected commit; generated skill and review artifacts are untracked under the repository's `skills/` directory and are not package source changes.
- **Required baseline:** CPU TensorFlow 2.x plus compiled StarDist 2D/3D extensions.
- **Optional surfaces:** TensorFlow CUDA execution, OpenCL/gputools, BioImage.IO, pretrained resource downloads, QuPath/ImageJ.

## Relative evidence used

- `README.md`, `extras/README.md`, `pyproject.toml`, `setup.py`, `setup.cfg`
- `stardist/models/base.py`, `stardist/models/model2d.py`, `stardist/models/model3d.py`
- `stardist/geometry/geom2d.py`, `stardist/geometry/geom3d.py`, `stardist/nms.py`, `stardist/matching.py`, `stardist/rays3d.py`, `stardist/utils.py`
- `stardist/scripts/predict2d.py`, `stardist/scripts/predict3d.py`, `stardist/bioimageio_utils.py`
- `extras/qupath_export_annotations.groovy`
- `tests/test_model2D.py`, `tests/test_model3D.py`, `tests/test_stardist2D.py`, `tests/test_stardist3D.py`, `tests/test_nms2D.py`, `tests/test_nms3D.py`, `tests/test_matching.py`, `tests/test_utils.py`, `tests/test_plot.py`, `tests/test_big.py`
- `examples/other2D/`, `examples/other3D/`, selected notebooks and README workflow sections

This record is deliberately free of local checkout, interpreter, and private environment paths so a future agent can use the relative evidence names to detect staleness.
