---
name: heatmap-visualization
description: "Configure, validate, run, and troubleshoot CLAM attention heatmap
  inference from trained checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# CLAM Heatmap Visualization

Use this sub-skill when the task is to create CLAM attention heatmaps, validate a heatmap YAML/process list, configure ROI or top-k patch sampling, explain `create_heatmaps.py` outputs, or diagnose heatmap failures caused by checkpoint, encoder, model, or slide-input mismatches.

## Route Tasks

- For heatmap YAML structure, process-list columns, model/encoder consistency, and safe preflight checks, read `references/configuration.md` and run `scripts/validate_heatmap_config.py`.
- For end-to-end heatmap commands, the interactive `Continue?` prompt, raw versus production outputs, ROI rendering, and sampled-patch outputs, read `references/workflows.md`.
- For checkpoint shape errors, missing UNI/CONCH settings, absent slides, ROI column problems, GPU memory issues, and heatmap rendering options, read `references/troubleshooting.md`.
- For patch-coordinate generation before heatmaps, use `../wsi-preprocessing/SKILL.md`.
- For pretrained encoder setup and feature-dimension choices, use `../feature-extraction/SKILL.md`.
- For training checkpoints and evaluation-time model arguments, use `../training-evaluation/SKILL.md`.

## Key CLAM Facts

- CLAM heatmaps are produced by `create_heatmaps.py --config_file <yaml-name>`, where the script resolves the config under `heatmaps/configs/`.
- Heatmap inference initializes a CLAM checkpoint, loads a pretrained encoder, scans slides or ROI regions with OpenSlide, computes attention scores, and writes both raw HDF5 assets and rendered production images.
- ResNet50-truncated and UNI features are 1024-dimensional; CONCH v1 features are 512-dimensional, so `model_arguments.embed_dim` must match the checkpoint and encoder family.
- The bundled validator is static and safe: it checks YAML/CSV shape and consistency without loading checkpoints, WSI files, OpenSlide, PyTorch, or encoders.
