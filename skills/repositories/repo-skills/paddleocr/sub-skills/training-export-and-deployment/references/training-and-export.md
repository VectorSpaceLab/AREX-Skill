# Training and Export Workflow

This reference is for maintainers or advanced users who need to inspect the config-driven training/export surface. It is not a substitute for actually running the job.

## Main entry points in the repository

- `tools/program.py` contains the shared YAML/config parsing logic.
- `tools/train.py` launches training.
- `tools/eval.py` runs evaluation.
- `tools/export_model.py` exports a trained model.
- `tools/infer*.py` and the `deploy/` tree hold legacy or deployment-focused evidence.

## Typical config structure

PaddleOCR-style configs usually include sections such as:

- `Global`
- `Architecture`
- `Train`
- `Eval`
- `Optimizer`
- dataset/reader definitions

The safe config helper in this sub-skill should summarize those sections without starting a full job.

## Common command patterns

```bash
python tools/train.py -c path/to/config.yml
python tools/eval.py -c path/to/config.yml -o Global.checkpoints=path/to/checkpoint
python tools/export_model.py -c path/to/config.yml -o Global.checkpoints=path/to/checkpoint
```

The exact flag set depends on the selected config family and the underlying PaddlePaddle / PaddleX backend.

## What to inspect before running

- Dataset paths and label files
- Checkpoint paths
- Output and save directories
- Device/backend flags
- Whether the selected config expects a detector, recognizer, structure model, or deployment-specific architecture

## Safe inspection workflow

1. Read the config summary with the bundled script.
2. Confirm dataset and checkpoint paths.
3. Decide whether the workflow is training, evaluation, or export.
4. Choose the backend and only then start the long-running command.

## Evidence to trust

- Source config files under `configs/`
- `tools/program.py` parsing behavior
- Safe YAML unit tests that reject dangerous YAML tags
- Deployment docs and TIPC evidence for backend selection
