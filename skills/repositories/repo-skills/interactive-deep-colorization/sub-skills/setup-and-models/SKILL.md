---
name: setup-and-models
description: "Guides Interactive Deep Colorization installation, backend choice,
  model artifact checks, and Docker or display setup before running colorization
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# setup-and-models

Use this sub-skill when a task is about preparing Interactive Deep Colorization rather than applying color hints: installing legacy dependencies, choosing Caffe versus PyTorch, checking required model files, deciding whether Docker/PyQt5 is a better route, or diagnosing setup failures.

## Route first

- Read [references/setup-reference.md](references/setup-reference.md) to choose a backend, dependency path, and model/runtime prerequisites.
- Read [references/model-artifacts.md](references/model-artifacts.md) before downloading, validating, or explaining model weights and expected filenames.
- Read [references/docker-reference.md](references/docker-reference.md) for the repository's Docker/PyQt5 variant and display-server caveats.
- Read [references/troubleshooting.md](references/troubleshooting.md) when Caffe, PyTorch, Qt, display, OpenCV, or missing-model errors block a workflow.

## Safe bundled script

- Run [scripts/check_model_artifacts.py](scripts/check_model_artifacts.py) to validate whether a checkout or staged artifact directory has the expected Caffe and PyTorch weight files. The script never downloads; it only checks file presence, size, and known paths.

## Boundaries

- For local-hints GUI, notebook-style API, mask/`ab` tensor, CLI-default, suggested-color, or saved-output questions, route to [../interactive-colorization/SKILL.md](../interactive-colorization/SKILL.md).
- For global histogram/reference-image transfer, route to [../global-histogram-transfer/SKILL.md](../global-histogram-transfer/SKILL.md).
- This sub-skill documents setup and safe validation. It does not certify that PyCaffe, PyQt GUI launch, Docker build, downloaded model inference, or network downloads work on the user's host.

## Key setup decisions

1. Decide backend intent:
   - `caffe` is the original SIGGRAPH 2017 backend and is required for the global histogram transfer notebook.
   - `pytorch` uses converted weights for the local-hints GUI path and avoids PyCaffe, but still needs the PyTorch weight file.
2. Decide UI path:
   - The root GUI script is PyQt4-based.
   - The Docker entry script is PyQt5-based and defaults to the PyTorch backend.
3. Validate assets before launching:
   - Use the bundled model checker for expected paths and missing files.
   - Do not launch GUI/notebooks first when model-weight errors are likely; missing weights usually fail only after expensive imports.
4. Treat training as out of scope:
   - The repository README points training to a separate PyTorch reimplementation repository; this generated skill covers inference/demo usage only.
