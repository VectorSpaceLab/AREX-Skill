# Compatibility Baseline

This repository was verified in a Python 3.7 environment. The source tree uses old Keras and TensorFlow APIs, so modern Keras 3 / TensorFlow 2.x combinations are not a safe default.

## Verified package baseline

- Python 3.7
- TensorFlow 1.15.5
- Keras 2.2.4
- NumPy 1.18.5
- h5py 2.10.0
- protobuf 3.20.3
- scipy 1.7.3
- scikit-learn 1.0.2
- opencv-python 4.5.5.64
- Pillow 9.5.0
- beautifulsoup4 4.12.2
- tqdm 4.66.4
- imageio 2.31.2
- matplotlib 3.5.3

## Backend expectations

- TensorFlow is the only supported backend in this repository.
- Theano and CNTK are explicitly unsupported.
- The custom layers and loss function expect TensorFlow-style Keras objects and old-style Keras backend helpers.

## Why older versions matter

- `keras.engine.topology` exists in Keras 2.x but not in Keras 3.
- TensorFlow 1.15.5 import compatibility requires `protobuf<=3.20.x`; newer protobuf releases break generated `_pb2` imports with a descriptor error.
- The source uses legacy TensorFlow symbols such as `tf.to_float` and `tf.log`, which are easiest to keep working under TensorFlow 1.15.
- Keras 2.2.4 is the verified baseline for this repository because the custom layers still call `keras.backend.image_dim_ordering()`.
- Several source files still use `np.bool`-style behavior, so very new NumPy releases are risky.
- The notebooks still reference `scipy.misc.imread`; modern SciPy versions removed it, so helper scripts should use `imageio` or Pillow instead.

## Minimal import smoke

From a checkout of this repository, a quick confidence check is:

```bash
python -c "import tensorflow as tf, keras; print(tf.__version__, keras.__version__)"
```

If that import fails, fix the environment before reading the deeper workflow references.
