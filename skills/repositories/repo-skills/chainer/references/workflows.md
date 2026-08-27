# Chainer Workflow Map

Use this file when you want the shortest path from a user request to the right Chainer sub-skill.

## 1. Core training and model building

Typical route: `Variable` or array input -> `Link` / `Chain` / `ChainList` model -> `Dataset` / `Iterator` -> `Optimizer` -> `Updater` -> `Trainer` -> extensions and serializers.

Use the `training` sub-skill for:

- define-by-run models and custom `forward` / `__call__` logic
- `chainer.links` and `chainer.functions`
- datasets, iterators, minibatch conversion, and dataset downloads
- `Trainer`, `Updater`, `Extension`, and trigger configuration
- CPU or GPU execution on a single host
- snapshots, `save_npz`, `load_npz`, and HDF5 persistence
- static-graph optimization examples

The bundled `scripts/training_smoke.py` is the recommended tiny end-to-end check.
The bundled `scripts/serialization_smoke.py` is the recommended persistence check.

## 2. Model export

Typical route: trained `Chain` or `Sequential` model -> ONNX or Caffe export -> file validation.

Use the `export` sub-skill for:

- `onnx_chainer.export(...)`
- `onnx_chainer.export_testcase(...)`
- ONNX opset limits and input / output naming
- `chainer.exporters.caffe.export(...)`
- export failures caused by unsupported layers or missing optional packages

The bundled `scripts/export_smoke.py` performs both ONNX and Caffe checks on a tiny model.

## 3. Distributed training

Typical route: MPI launch -> communicator creation -> device placement -> multi-node optimizer -> optional dataset scattering and evaluator wrapping.

Use the `distributed` sub-skill for:

- ChainerMN communicator selection
- `create_multi_node_optimizer(...)`
- `scatter_dataset(...)` and `scatter_index(...)`
- `create_multi_node_evaluator(...)`
- `MultiNodeChainList` and `create_multi_node_n_step_rnn(...)`
- CPU-only `naive` communicator versus GPU `pure_nccl` workflows
- MPI, `mpi4py`, and `mpiexec` troubleshooting

The bundled `scripts/chainermn_probe.py` checks the local MPI and CuPy prerequisites before you try a real launch.

## 4. ChainerX

Typical route: decide whether ChainerX is built -> inspect devices/backends -> use `chainerx.ndarray` or Chainer-backed device helpers -> respect ChainerX limitations.

Use the `chainerx` sub-skill for:

- source build flags such as `CHAINER_BUILD_CHAINERX` and `CHAINERX_BUILD_CUDA`
- device parsing with `native:0` or `cuda:0`
- `using_device`, `get_default_device`, and `set_default_device`
- fallback between Chainer, NumPy, CuPy, and ChainerX
- ChainerX limitations such as dtype and in-place update constraints

The bundled `scripts/chainerx_probe.py` reports whether ChainerX is importable and what to fix if it is not.

## 5. Checkout and maintenance tasks

If the user is editing the repository itself rather than using the library, keep the core sub-skills in mind but start from the repository-level install and troubleshooting references.

Useful maintainer-oriented checks:

- `python -m pip install -e .` or a wheel build from a clean checkout
- `python -m pytest` on focused `tests/` subsets
- `setup.py` build knobs such as `CHAINER_BUILD_CHAINERX`
- `setup.cfg` test markers and warnings filters
- `scripts/ci/` files as reference-only evidence for CI behavior, not as runtime skill helpers

The bundled `scripts/runtime_probe.py` is the fastest first check for a checkout that will not import cleanly.

## 6. Example families worth remembering

The repo's examples cluster into a few common workflows:

- MNIST and CIFAR: single-node training, custom loops, and GPU usage
- PTB, seq2seq, text classification, and word2vec: recurrent or NLP training
- Serialization: save and load `npz` and `hdf5` snapshots
- ImageNet and model zoo evaluation: larger vision workflows and external weights
- Reinforcement learning, DCGAN, VAE, image captioning, and wavenet: larger model-specific recipes
- ChainerMN examples: distributed MNIST, parallel convolution, seq2seq, and ImageNet
- Static graph optimization examples: decorated training loops for repeated schedules

Use the examples as evidence and validation targets, but prefer the bundled smoke scripts for future runtime use.
