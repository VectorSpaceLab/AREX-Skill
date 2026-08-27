# Repository provenance

`schema: disco.repo-provenance.v1`

- Repository: `charlesq34/frustum-pointnets`
- Remote URL: `https://github.com/charlesq34/frustum-pointnets.git`
- Source commit: `2ffdd345e1fce4775ecb508d207e0ad465bcca80`
- Source branch: `master`
- Exact tag: none detected at the source commit
- Source checkout state during creation: dirty only because generated `skills/` artifacts were added; source files were not intentionally modified
- Package version: not applicable; the repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, or declared distribution metadata
- Public source identity: CVPR 2018 Frustum PointNets for 3D object detection from RGB-D data
- Evidence paths: `README.md`, `dataset/README.md`, `models/`, `models/tf_ops/`, `kitti/`, `train/`, `train/kitti_eval/`, `sunrgbd/`, `mayavi/`, `scripts/`
- Runtime baseline used for inspection: isolated Python 3.7/TensorFlow 1.15 CPU graph environment with legacy-compatible NumPy/SciPy/OpenCV/Pillow/protobuf versions; this private environment is intentionally not part of the public skill contract
- Known refresh signals: source commit, TensorFlow-era assumptions, custom-op compile scripts, direct `cPickle` imports, KITTI/SUN RGB-D data schemas, and native CLI flags

The generated skill is self-contained. The evidence paths identify the source
revision used for refresh decisions; runtime instructions do not require the
original checkout, its datasets, compiled binaries, or its environment.
