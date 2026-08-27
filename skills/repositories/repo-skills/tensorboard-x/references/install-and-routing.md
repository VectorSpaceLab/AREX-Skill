# Install and Routing

This reference is the shared starting point for tensorboardX users who want to verify the package, choose the right workflow route, and install only the dependencies their task really needs.

## Install and import check

Base install:

```bash
python -m pip install tensorboardX
```

Minimal import check:

```bash
python -c "from tensorboardX import SummaryWriter; print(SummaryWriter)"
```

Install TensorBoard if you want to inspect event files with the standard viewer:

```bash
python -m pip install tensorboard
```

Use the bundled inspection helper when you want a quick readable check of the active environment:

```bash
python scripts/tbx_inspect_install.py
```

## Optional dependency map

Install these only when the selected workflow needs them.

| Workflow | Typical extra packages |
| --- | --- |
| `logging-core` | none beyond the base package; `tensorboard` is helpful for local inspection |
| `rich-media-summaries` | `pillow`, `matplotlib`, `soundfile`, `moviepy`, `imageio>=2.29.0` |
| `graph-and-embedding-plugins` | `torch`, `tensorboard`, `onnx` if you need ONNX file loading |
| `remote-and-parallel-integrations` | `boto3`, `moto<5`, `comet-ml`, `google-cloud-storage` only when the integration is actually used |

Notes:

- `torch` is needed for PyTorch graph and embedding workflows, not for plain scalar logging.
- `moviepy` and `imageio` are only needed for video summaries.
- `soundfile` is only needed for audio summaries.
- `boto3` and `moto<5` are only needed for S3-path or mock-cloud checks.
- `comet-ml` and `google-cloud-storage` are credentialed or service-backed integrations; keep them disabled unless the user explicitly needs them.

## Route selection guide

| Task cue | Route |
| --- | --- |
| scalar logging, `SummaryWriter`, `use_metadata`, `purge_step`, `write_to_disk=False` | `logging-core` |
| image, audio, video, histogram, PR curve, text, mesh | `rich-media-summaries` |
| `add_graph`, `add_embedding`, `add_onnx_graph`, `add_openvino_graph` | `graph-and-embedding-plugins` |
| `GlobalSummaryWriter`, multiprocessing, `s3://`, `gs://`, Comet | `remote-and-parallel-integrations` |

## Safe operating assumptions

- Use TensorBoardX as a Python library, not a CLI package.
- Keep the runtime self-contained; do not rely on the original checkout or its examples.
- Prefer a local temporary logdir unless the user explicitly asks for remote storage.
- Treat Comet, S3, and GCS as opt-in integrations.

## When to read this reference

Read this file first when you are deciding which sub-skill to open, when the user asks about installation, or when an install/import check is failing before you know which workflow family is involved.
