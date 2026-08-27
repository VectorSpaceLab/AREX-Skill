# Development and Packaging Notes

These notes are for maintainers or agents editing VSE itself. They are not
required for ordinary extraction, OCR backend selection, GUI operation, or
subtitle synchronization.

## Evidence-backed build variants

The repository contains Windows CI workflows for:

- CPU builds using Python 3.12 and PaddlePaddle CPU.
- CUDA builds for CUDA 10.2, 11.8, and 12.6 with matching PaddlePaddle GPU
  wheels in the workflow.
- DirectML builds using CPU PaddlePaddle plus `requirements_directml.txt`.

The build workflows install requirements, freeze dependencies, use QPT tooling,
call `backend/tools/makedist.py`, download packages into release output trees,
and package release/debug outputs with 7z.

## Why packaging scripts are reference-only

`backend/tools/makedist.py` and the CI shell snippets mutate build output
directories, download large dependency sets, and assume Windows release tooling.
This repo skill does not bundle or wrap those scripts as ordinary runtime
helpers. Use them only when the user explicitly asks to maintain VSE packaging.

## Source editing cautions

- Keep GUI, backend extraction, OCR/model configuration, and Sushi sync changes
  routed to their owning areas.
- Do not update backend install guidance without checking both README variants
  and CI workflows.
- Changes to `backend/config.py` can affect GUI settings, CLI extraction, OCR
  thresholds, model selection, output behavior, and translation labels.
- Changes to `backend/tools/paddle_model_config.py` should be validated against
  bundled model directory names and representative language codes.
