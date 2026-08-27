# Troubleshooting

This file collects the cross-cutting failures that show up across multiple Chainer workflows.
Use the sub-skill troubleshooting pages for workflow-specific details.

## `import chainer` fails

Common causes:

- The environment is using an unsupported Python version for Chainer 7.x.
- `setuptools`, `pip`, or `pkg_resources` are missing or outdated.
- The package was installed from source without the right build flags.
- The checkout is being imported directly instead of the installed package.

Recovery:

- Prefer a supported Python version from the docs.
- Reinstall the package with `pip install chainer` or a clean source build.
- Run `scripts/runtime_probe.py` to see which backend flags are actually active.

## CUDA or cuDNN is unavailable

Symptoms:

- `chainer.backends.cuda.available` is `False`.
- `chainer.backends.cuda.cudnn_enabled` is `False`.
- GPU examples or `to_gpu()` fail.

Likely causes:

- CuPy was not installed.
- The installed CuPy wheel does not match the CUDA runtime.
- cuDNN is missing or not visible to CuPy.

Recovery:

- Install a matching CuPy wheel such as `cupy-cudaXX`.
- Reinstall CuPy with cuDNN support if you need cuDNN.
- If you only need CPU workflows, keep the CPU path and avoid GPU-only examples.

## HDF5 persistence is missing

Symptoms:

- `save_hdf5` or `load_hdf5` fails.
- The serializer examples complain about `h5py`.

Likely cause:

- `h5py` is not installed.

Recovery:

- Install `h5py` and rerun the persistence check.
- Use `save_npz` / `load_npz` if HDF5 is not required.

## ONNX export fails

Symptoms:

- `onnx_chainer.export(...)` raises `ImportError` or `ValueError`.
- Exported graphs do not pass the ONNX checker.
- Opset warnings appear.

Likely causes:

- `onnx` is missing or too new for the supported Chainer pin.
- The selected opset is outside the supported range.
- The model uses a function or layer that the exporter cannot convert.

Recovery:

- Install `onnx<1.7.0` when you need the legacy exporter.
- Use `export_testcase(...)` for a more complete export artifact.
- Start with the bundled `scripts/export_smoke.py` and a tiny toy model before trying a large model.

## Caffe export fails

Symptoms:

- `chainer.exporters.caffe.export(...)` raises a conversion error.
- The output directory is missing `chainer_model.prototxt` or `chainer_model.caffemodel`.

Likely causes:

- The model uses a layer or function not supported by the legacy exporter.
- The input is not wrapped the way the exporter expects.

Recovery:

- Compare the model to the supported layer families documented in the export reference.
- Use a tiny model first and confirm the export script succeeds.

## ChainerMN or MPI fails

Symptoms:

- `mpi4py` cannot be imported.
- `mpiexec` or `mpicc` is missing.
- Workers hang or abort during startup.
- GPU communication fails because NCCL or CUDA-aware MPI is absent.

Likely causes:

- MPI and `mpi4py` were not installed together.
- The MPI runtime is not CUDA-aware for GPU workflows.
- The launch command is not using `mpiexec` / `mpirun` correctly.

Recovery:

- Confirm that `mpiexec` and `mpicc` exist before attempting a real run.
- Install `mpi4py` against the same MPI runtime you will use at execution time.
- For GPU runs, confirm CuPy and NCCL are present.
- For CPU-only debugging, use the `naive` communicator.
- If an uncaught exception leaves MPI workers hanging, use `python -m mpi4py yourscript.py` or enable `chainermn.global_except_hook.add_hook()`.

## ChainerX is unavailable

Symptoms:

- `chainerx.is_available()` is `False`.
- Importing `chainerx` reports that `_build_info.py` or `_core` is missing.
- `native:0` or `cuda:0` device workflows fail.

Likely causes:

- ChainerX was not built into the installed package.
- The source build omitted `CHAINER_BUILD_CHAINERX=1`.
- CUDA support for ChainerX was not enabled.

Recovery:

- Rebuild from source with the ChainerX build flags enabled.
- If you do not need ChainerX, use ordinary Chainer arrays and backend helpers instead.

## Static graph and ChainerX conflict

ChainerX is not supported by the static subgraph optimization feature.
If a model depends on ChainerX, set `chainer.config.use_static_graph = False`.

## Helpful quick checks

- `python -c 'import chainer; print(chainer.__version__)'`
- `python scripts/runtime_probe.py`
- `python scripts/training_smoke.py`
- `python scripts/export_smoke.py --format onnx`
- `python scripts/chainerx_probe.py`
- `python scripts/chainermn_probe.py`
