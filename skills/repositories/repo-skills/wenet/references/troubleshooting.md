# WeNet Cross-Cutting Troubleshooting

Read this for problems that can affect multiple WeNet workflows before routing
to a sub-skill-specific troubleshooting page.

## Installation and import

- Prefer Python versions compatible with WeNet's ML stack; Python 3.10/3.11 are
  safer than bleeding-edge Python for PyTorch/Torchaudio projects.
- If importing WeNet fails with a PyTorch internal API error, align PyTorch and
  Torchaudio with WeNet's documented training/deployment recommendation instead
  of accepting the newest resolver result blindly.
- If PyTorch warns that NumPy 2.x is incompatible with modules compiled against
  NumPy 1.x, pin `numpy<2` unless the whole environment is known to support
  NumPy 2.x.
- Run the shared checker:

  ```bash
  python scripts/check_wenet_environment.py --device cpu
  ```

## Optional backends

WeNet exposes CPU, CUDA, and NPU choices in package/training CLIs and has many
runtime backends. Parser support does not prove backend availability.

- CUDA requires a compatible PyTorch/ONNX Runtime/TensorRT stack and driver.
- Ascend NPU requires CANN and matching `torch-npu` versions.
- OpenVINO, IPEX, Horizon BPU, Kunlun XPU, Android, iOS, and Triton/TensorRT
  require target-specific SDKs/toolchains.
- If hardware is unavailable, keep the workflow on CPU or mark the accelerator
  path as planned but unverified.

## Data/config/model mismatch

Many failures come from mixing artifacts from different runs:

- `train.yaml` must match the checkpoint.
- `units.txt` and tokenizer resources must match the model config.
- `data.list` schema and `data_type` must match training/recognition flags.
- Export chunk/cache settings must match runtime streaming settings.

Route schema problems to `sub-skills/data-preparation/`, training and decode
problems to `sub-skills/training-and-decoding/`, export preflight to
`sub-skills/model-export/`, and runtime artifact pairing to
`sub-skills/runtime-deployment/`.

## Network, downloads, and long jobs

Built-in package models, public datasets, LM resources, and runtime SDKs can
trigger downloads. Full training, shard packaging, CMVN over large corpora,
ONNX/TensorRT conversion, and runtime builds can be long-running. Confirm user
approval for network, storage, hardware, and time before launching these steps.
