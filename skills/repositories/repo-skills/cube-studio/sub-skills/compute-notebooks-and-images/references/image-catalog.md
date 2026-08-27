# Image catalog

This document covers CubeStudio image registry management, curated notebook image families, and safe notes for online image builds.

## Registry and repository management

Two model layers matter here:

| Model | Role |
| --- | --- |
| `Repository` | Registry host, username, password, and the Kubernetes pull-secret name (`hubsecret`). |
| `Images` | Curated reusable image entry with a category, name, Dockerfile content, and optional git link. |
| `Docker` | Online debug / commit / push workflow for building an image from a live container. |

Key behaviors:

- `Repository.apply_hubsecret()` propagates the pull secret across namespaces.
- `Repository.server` must match the registry host portion of the target image.
- `Images.image_type` categories include `dev`, `jupyter`, `job-template`, `pipeline`, `automl`, `service`, and `inference`.
- `Docker.pre_add()` warns when the target image host does not match a known repository.
- `Docker.debug()` starts a privileged debug pod using the source image and the project's notebook-oriented placement rules.
- `Docker.save()` commits the live container to the target image and pushes it with the configured CLI.

## Notebook and IDE families

The curated notebook catalog is driven by `NOTEBOOK_IMAGES`.

Representative families:

| Family | Example images | Notes |
| --- | --- | --- |
| Jupyter CPU | `notebook:jupyter-ubuntu22.04` | Default CPU notebook family. |
| Jupyter GPU | `notebook:jupyter-ubuntu22.04-cuda11.8.0-cudnn8` | GPU notebook family with CUDA / cuDNN support. |
| Jupyter big data | `notebook:jupyter-ubuntu-bigdata` | Spark / Hive / Flink oriented notebook image. |
| Jupyter ML | `notebook:jupyter-ubuntu-machinelearning` | Curated machine-learning notebook with common data-science packages. |
| Jupyter DL | `notebook:jupyter-ubuntu-deeplearning` | Deep-learning notebook with TensorFlow / PyTorch-style packages. |
| Theia / VS Code CPU | `notebook:vscode-ubuntu-cpu-base` | Theia editor on the CPU base. |
| Theia / VS Code GPU | `notebook:vscode-ubuntu-gpu-base` | Theia editor on the GPU base. |
| Commercial variants | `enterprise-jupyter-ubuntu-cpu-pro`, `enterprise-matlab-ubuntu-deeplearning`, `enterprise-rstudio-ubuntu-bigdata` | Keep these as catalog entries only; follow the product policy of the running deployment. |

Build helpers and image families:

- `images/jupyter-notebook/build.sh` builds CPU and GPU conda notebook variants.
- `images/ubuntu-gpu/build.sh` builds CUDA base images and Python-tagged variants.
- `images/jupyter-notebook/*/Dockerfile` layers examples and init scripts onto the base notebook image.
- `images/theia/*` defines the CPU and GPU Theia base images.
- `images/jupyter-notebook/init.sh` sets notebook SSH behavior and links the example bundle into the user workspace.

## Catalog selection rules

- `NOTEBOOK_IMAGES` may be a list of `[image, label]` pairs or a nested cascade dictionary.
- The UI maps image strings back to friendly notebook labels.
- `ide_type` is inferred from the image string when the record is created.
- Keep notebook and IDE catalog entries separate from serving / inference images.

## Cross-route note

The `images/serving/**` tree is not owned by this sub-skill.
Route service-side serving image questions to `serving-aihub-and-llm`; only mention them here as a cross-reference when necessary.
