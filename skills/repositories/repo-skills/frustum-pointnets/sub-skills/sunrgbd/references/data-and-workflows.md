# SUN RGB-D data and workflows

## External preparation

The README requires SUNRGBD V1 plus its external toolkit. MATLAB extraction
creates the raw frame/annotation layout; then move generated subfolders under a
`mysunrgbd/training/` tree and create train/validation file lists. The Python
preparation module generates zipped pickle files for the TensorFlow pipeline.
The repository checkout contains examples and some derived assets, not a
portable raw SUNRGB-D distribution.

The Python detection code uses 10 SUN object classes and one-hot vectors. Keep
class ordering, mean box dimensions, point count, and RGB/no-RGB channel choice
consistent between generated data, training, and testing. Detector-frustum
validation requires amodal 2D boxes; raw RGB images alone are insufficient.

## Entry-point intent

- `sunrgbd_data.py`: prepare point-cloud/frustum pickle assets; data-dependent
  and potentially long-running.
- `train_one_hot.py`: TensorFlow-1 training; default point count 2048, batch 32,
  151-ish epoch workflow per README (the source default is 250), Adam, and
  optional `--no_rgb`.
- `test_one_hot.py`: checkpoint-backed validation; `--dump_result` writes a
  prediction pickle.
- `evaluate.py`: consumes data and result pickle paths and can use
  `--from_rgb_detection`.
- `viz.py`/`viz_eval.py`: optional interactive error visualization.

Use the bundled checker to validate only the presence and naming of supplied
assets. It does not parse or modify generated pickle contents.
