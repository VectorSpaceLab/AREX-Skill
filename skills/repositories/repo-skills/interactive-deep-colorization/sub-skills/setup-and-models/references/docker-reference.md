# Docker Reference

## Purpose

Read this when a user asks about the repository's Docker path, PyQt5 conversion, display forwarding, or why Docker behaves differently from the root GUI script.

## What the Docker variant changes

The Docker subtree contains a separate GUI entry point that mirrors the root app but imports PyQt5 widgets instead of PyQt4. Its parser mostly matches the root script, but its default backend is `pytorch` instead of `caffe`.

Important differences:

- Root script: PyQt4, qdarkstyle imported and stylesheet loaded, backend default `caffe`.
- Docker entry script: PyQt5, qdarkstyle stylesheet call commented out, backend default `pytorch`.
- Docker model helper only fetches `caffemodel.pth` for the PyTorch path, not all Caffe/global artifacts.
- Docker launch needs a display server forwarding configuration; container startup alone is not enough for GUI rendering.

## Distilled Docker flow

A user-approved Docker workflow generally has these phases:

1. Stage or fetch the PyTorch model file expected by the Docker path.
2. Build the image from the repository's Docker context.
3. Configure host display forwarding before running the container.
4. Run the image with a `DISPLAY` environment value appropriate for the host.

The repository's Docker README was written for macOS/XQuartz-style GUI forwarding. On Linux, the display forwarding command and permissions may differ. On remote/headless servers, a virtual display or non-GUI notebook/API path may be safer.

## Display and runtime cautions

- `xhost + ...` relaxes display-server access. Use it only when the user understands the trust boundary and host-specific implications.
- Docker build may download packages and model files, so it is not a safe implicit verification step.
- A successful Docker build does not guarantee the GUI can connect to the host display.
- The Docker PyQt5 code is a compatibility variant, not a complete rewrite of the model API.

## When not to use Docker

Prefer non-Docker source/API guidance when the user only needs to inspect CLI defaults, tensor shapes, model artifact names, or local-hints notebook logic. Prefer a notebook/API path when the user is on a headless server and does not need the interactive GUI.

## Docker troubleshooting quick table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Container starts but no GUI appears | `DISPLAY` not forwarded or host display permissions not configured | Verify host display server, container `DISPLAY`, and access control separately. |
| PyTorch model file missing inside container | Docker helper fetched only one file or download was skipped/failed | Use the model artifact checker against the staged Docker context. |
| Caffe global workflow requested in Docker | Docker path is PyTorch-oriented by default and does not prepare Caffe/global weights | Route to setup/model artifact guidance and global histogram transfer prerequisites. |
| Import errors mention PyQt4 inside Docker | Running the root script rather than Docker PyQt5 entry script | Use the Docker entry script or install the matching Qt binding. |
