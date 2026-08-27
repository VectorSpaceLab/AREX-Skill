# Installation and Compatibility

## Purpose

Read this before trying to import DeepCTR or choose a backend-specific workflow. It summarizes the public installation and runtime facts that were verified from the package metadata, docs, examples, tests, and live inspection.

## Verified package facts

- Distribution name: `deepctr`
- Import name: `deepctr`
- Version represented by this skill: `0.9.4`
- Python support advertised by the package: `>=3.7`
- TensorFlow support advertised by the package: `1.15` and `2.x`
- TensorFlow is installed separately from DeepCTR
- Public Keras APIs should come from `tensorflow.keras`

## Practical installation baseline

DeepCTR works best when TensorFlow is installed first and already matches the user's Python version, NumPy range, and CPU/GPU stack.

A practical baseline for many modern CPU environments is:

```bash
python -m pip install "numpy<2" "tensorflow<2.21"
python -m pip install deepctr
```

If TensorFlow has a tighter NumPy requirement for the selected release, follow TensorFlow's own requirement instead of forcing `numpy<2`.

## h5py and Python notes

- For Python `>=3.9`, DeepCTR allows `h5py>=3.7.0`.
- On older Python versions, follow the `h5py` constraint required by the installed TensorFlow release.
- If `pip` reports a NumPy or h5py conflict, fix the TensorFlow side first, then reinstall DeepCTR.

## GPU notes

- GPU use is optional for most DeepCTR workflows.
- If you need GPU acceleration, install a TensorFlow build that matches your CUDA/cuDNN platform, then verify that TensorFlow actually sees GPU devices.
- Multi-GPU examples are optional and training-heavy; do not use them as the default smoke path.

## Legacy Estimator note

DeepCTR also exposes a legacy TensorFlow Estimator surface under `deepctr.estimator`, but that path is version-sensitive and depends on top-level `tf.estimator` availability in the installed TensorFlow runtime. If you need Estimator workflows, run the estimator probe script from the generated skill tree first.

## Minimal verification

```bash
python scripts/check_deepctr_env.py --json
```

That check confirms the import surface, representative constructor signatures, and optional backend visibility without depending on source-repository example files.
