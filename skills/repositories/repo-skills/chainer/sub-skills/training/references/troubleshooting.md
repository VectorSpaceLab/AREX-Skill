# Training Troubleshooting

## Import or device issues

If `import chainer` fails, start with the root troubleshooting page and the `scripts/runtime_probe.py` output.
If `chainer.backends.cuda.available` is `False`, the model can still train on CPU, but GPU-specific examples will fail until CuPy is installed.
If `chainer.backends.cuda.cudnn_enabled` is `False`, GPU training still works but cuDNN-accelerated paths are unavailable.

## Bad configuration values

Common configuration mistakes:

- `use_cudnn` must be one of `always`, `auto`, or `never`.
- `use_ideep` must be one of `always`, `auto`, or `never`.
- `dtype` must be one of `float16`, `float32`, `float64`, or `mixed16`.

The docs and tests expect `chainer.using_config(...)` or `chainer.config` to carry these values.

## Trainer runtime errors

- `Trainer.elapsed_time` raises `RuntimeError('training has not been started yet')` if you query it too early.
- Extensions such as `PrintReport` or `Evaluator` must be attached to the correct trainer and iterator objects.
- When the model is wrapped in `Classifier`, the reported keys are typically `main/loss` and `main/accuracy`.

## Serialization problems

Symptoms:

- `save_hdf5` or `load_hdf5` fails.
- Persistent values disappear after loading.
- `load_npz` does not restore the expected model state.

Recovery:

- Make sure `h5py` is installed before using HDF5 serialization.
- Register extra state with `add_persistent(...)` if it must survive a save/load cycle.
- Keep the model class structure stable between save and load.

## Example-specific issues

- MNIST and CIFAR examples often assume a downloadable dataset helper.
- PTB and seq2seq examples may rely on cached text data.
- ImageNet and model-zoo recipes often assume an external list file, pretrained weights, or a mean file.

Use the bundled smoke scripts first when you only need to validate the core training stack.

## Quick recovery path

1. Run `scripts/runtime_probe.py`.
2. Run `scripts/training_smoke.py`.
3. Run `scripts/serialization_smoke.py`.
4. If the issue is GPU-only, confirm CuPy and cuDNN separately.
