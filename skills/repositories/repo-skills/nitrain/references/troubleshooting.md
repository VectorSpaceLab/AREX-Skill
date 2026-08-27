# Troubleshooting

## Purpose

Use this for cross-cutting install, import, and backend issues that affect more than one Nitrain workflow. Workflow-specific data-shape or API mistakes are documented in the nearest sub-skill reference.

## Common failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: google.cloud.storage` or `google.oauth2` | `google-cloud-storage` / `google-auth` were not installed explicitly. | Install the base data stack from `references/installation.md` and rerun `python -m pip check`. |
| `pip check` reports `antspynet`, `antspyx`, `protobuf`, or `tensorflow` conflicts | A newer PyPI stack was installed than the current repo snapshot supports. | Use the verified CPU pins from `references/installation.md`, especially `antspyx==0.5.4`, `antspynet==0.2.9`, `tensorflow==2.17.0`, and `tf-keras==2.17.0`. |
| `pip check` reports `google-api-core`, `googleapis-common-protos`, `proto-plus`, or `protobuf` conflicts | The latest Google Cloud stack pulled a protobuf range that clashes with TensorFlow 2.17.0. | Pin `google-cloud-storage==2.14.0`, `google-api-core==2.15.0`, `googleapis-common-protos==1.62.0`, and `proto-plus==1.23.0`. |
| `Trainer` or `Loader.to_keras()` cannot import TensorFlow | The Keras/TensorFlow stack is missing. | Install `tensorflow==2.17.0` and `tf-keras==2.17.0`, then rerun the smoke helper. |
| `TorchTrainer` or MONAI import fails | The CPU Torch/MONAI stack is missing. | Install `torch==2.8.0+cpu` and `monai==1.6.0`, then rerun `scripts/check_install.py --mode torch`. |
| `pip check` reports `monai ... requires torch>=2.8.0` | An older torch wheel was installed. | Install `torch==2.8.0+cpu` from the CPU wheel index before `monai`. |
| `nitrain.fetch_pretrained` is not callable | In this release, `nitrain.fetch_pretrained` is the imported module object, not the function. | Import the function from `nitrain.models.fetch_pretrained import fetch_pretrained`. |
| `nitrain.TorchTrainer` is missing | The class is exported from the `nitrain.trainers` submodule, not the package root. | Use `from nitrain.trainers import TorchTrainer`. |
| README examples mention `tx.RandomNoise` | That transform is not present in the inspected source tree. | Use the random transforms that actually exist: `RandomCrop`, `RandomRotate`, `RandomZoom`, `RandomFlip`, `RandomTranslate`, and `RandomShear`. |
| TensorFlow prints CPU/GPU warnings about missing CUDA or TensorRT | This host is CPU-only for the verified path. | Treat the warning as expected unless you explicitly selected a CUDA workflow. |
| `fetch_data('openneuro/...')` hangs or fails | That path depends on `datalad`, `git-annex`, and network access. | Install the optional tools and retry only if the workflow actually needs OpenNeuro. |
| `GoogleCloudDataset` fails with 403/404/credential errors | The bucket path or service-account credentials are missing or invalid. | Confirm the JSON credentials, bucket name, and object path; this is not a local package bug. |

## How to debug safely

1. Run `python -m pip check` inside the target environment.
2. Run `python scripts/check_install.py --mode base` to confirm the core import path.
3. Add one workflow at a time: `--mode datasets`, `--mode preprocess`, `--mode models`, or `--mode predictor`.
4. If a failure mentions missing cloud/network resources, stop at the boundary of the local package and document the external prerequisite instead of guessing.

## Notes that should not be forgotten

- A successful import of `nitrain` alone does not mean every workflow dependency is present.
- The verified snapshot is CPU-only; TensorFlow and Torch warnings about unavailable GPUs are expected.
- If a future checkout changes the package metadata or export surface, refresh the skill before relying on these fixes.
