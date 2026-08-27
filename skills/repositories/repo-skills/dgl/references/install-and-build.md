# DGL Install And Build Reference

## When To Read

Read this before installing DGL, selecting a backend, using GraphBolt or sparse extensions, installing DGL-Go, or building DGL from source.

## Public Install Choices

DGL publishes CPU and CUDA builds under the same package name. Use the official selector for production installs, and verify the backend after installation:

```bash
python -m pip install dgl
python - <<'PY'
import dgl
print('dgl', dgl.__version__)
print('backend', dgl.backend.backend_name)
PY
```

DGL documentation states support for Python 3.7 through 3.11 in this checkout's install guide. Modern Python versions beyond that may work for newer wheels, but do not assume source-build or extension compatibility unless the installed package proves it.

## Backend Selection

DGL supports PyTorch, MXNet, and TensorFlow backends in the source documentation, with PyTorch as the main backend used by GraphBolt, DGL sparse, distributed training, and DGL-Go workflows.

Backend priority:

1. Set `DGLBACKEND=pytorch`, `DGLBACKEND=mxnet`, or `DGLBACKEND=tensorflow` for one command.
2. Set the same environment variable globally in the shell or service.
3. Use `python -m dgl.backend.set_default_backend BACKEND` to write the DGL config file.

For PyTorch workflows, install a compatible `torch` first when a DGL wheel or GraphBolt library expects a specific ABI.

## GraphBolt And Torch ABI

GraphBolt loads a native library named for the PyTorch version, such as `libgraphbolt_pytorch_2.2.1.so`. If `import dgl` fails with a missing `libgraphbolt_pytorch_<version>` path:

- Check `python -c "import torch; print(torch.__version__)"`.
- Check whether the installed DGL wheel contains a matching GraphBolt library.
- Install a DGL wheel compatible with the desired torch version, or pin torch to a version supported by that DGL wheel.
- Do not paper over the error by disabling GraphBolt if the task needs GraphBolt, dataloading, or distributed APIs that import it.

## DGL Sparse

`dgl.sparse` depends on DGL's sparse native extension and PyTorch. Use a quick smoke check before writing sparse workflows:

```bash
python - <<'PY'
import torch
import dgl.sparse as dglsp
A = dglsp.spmatrix(torch.tensor([[0, 1], [1, 2]]), shape=(3, 3))
print(A.shape, A.nnz)
PY
```

If sparse import fails, align DGL, torch, and the native extension; then route workflow details to `sub-skills/message-passing-training/`.

## DGL-Go Install

DGL-Go is a separate command-line package that provides the `dgl` console command for `configure`, `recipe`, `train`, `export`, `configure-apply`, and `apply`.

```bash
python -m pip install dglgo
python -m pip install dgl
```

DGL-Go can pull optional training and scientific dependencies such as OGB, RDKit, scikit-learn, Typer, YAML tooling, and PyTorch. Install it only when the task needs CLI experiments or config generation. For safe YAML preflight without installing the full optional stack, use `sub-skills/dglgo-cli/scripts/dglgo_config_linter.py`.

## Source Build Overview

A source build is needed when editing native code, testing unreleased C++/GraphBolt/sparse changes, or building a wheel for an unsupported backend/platform.

Public source-build sequence from DGL docs:

```bash
git clone --recurse-submodules https://github.com/dmlc/dgl.git
cd dgl
bash script/create_dev_conda_env.sh -c
bash script/build_dgl.sh -c
cd python
python setup.py install
python setup.py build_ext --inplace
```

CUDA builds use `script/create_dev_conda_env.sh -g CUDA_VERSION` and `script/build_dgl.sh -g`. Do not start a source build automatically if submodules, CMake, compilers, CUDA toolkit, or the requested backend are not confirmed.

## Native Library Search

DGL's Python package looks for `libdgl` in packaged library directories, `DGL_LIBRARY_PATH`, platform library paths, source build directories such as `build/` and `build/Release`, and the install prefix. If source import or editable install fails with `Cannot find the files` and a list of `libdgl.so` candidates, the native library has not been built or is not discoverable.

Recovery steps:

1. Confirm submodules are initialized when building from source.
2. Build CPU or CUDA shared libraries.
3. Set `DGL_LIBRARY_PATH` only for local source development sessions.
4. Prefer a published wheel when the task is normal package usage rather than repo development.

## CUDA And GPU Notes

- DGL CPU inspection can cover most API routing and smoke checks.
- CUDA tasks require compatible driver, CUDA runtime/toolkit, PyTorch CUDA wheel, and DGL CUDA build.
- GPU-based neighbor sampling with classic `dgl.dataloading.DataLoader` requires graph/train IDs/device placement and `num_workers=0`.
- GraphBolt neighbor sampling GPU support differs by version; route detailed decisions to `sub-skills/dataloading-graphbolt/`.

## Build Scripts Classification

- `script/build_dgl.sh`: source-build reference only; it runs CMake and Make and can be long-running.
- `script/create_dev_conda_env.sh`: development environment reference only; it mutates conda environments and installs broad dependencies.
- `script/run_pytest.sh`: maintainer test reference only; it assumes a built checkout and sets source-tree environment variables.

Future agents should not need these source scripts for ordinary DGL package usage; use bundled skill scripts for safe diagnostics.
