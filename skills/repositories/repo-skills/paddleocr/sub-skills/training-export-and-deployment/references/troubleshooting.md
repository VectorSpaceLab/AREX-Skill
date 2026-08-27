# Training, Export, and Deployment Troubleshooting

## YAML or config parsing errors

### Symptom
- The config loader rejects the YAML file.
- A command fails before training starts.

### Likely causes
- The config has invalid syntax or unsupported keys.
- A dangerous YAML tag or alias was used.

### Recovery
- Use the bundled config-inspection script to validate the file structure first.
- Keep the config in the same family as the selected model or pipeline.

## Missing datasets or checkpoints

### Symptom
- Training or export fails when a dataset or checkpoint path is missing.

### Likely causes
- `Train`, `Eval`, or `Global.checkpoints` points to a path that does not exist.
- The config references an artifact from a different model family.

### Recovery
- Confirm the dataset layout and checkpoint path before rerunning.
- Start from the config summary instead of the launch command.

## Backend and device problems

### Symptom
- Training or deployment only works on one device family.
- A backend-specific flag appears to be ignored.

### Likely causes
- The selected config or export path does not support the requested backend.
- The runtime lacks the accelerator or inference engine required by the model.

### Recovery
- Treat GPU or accelerator runs as backend-specific verification, not as a CPU import assumption.
- Choose the deployment path that matches the backend documented for the model family.

## Build or deployment failures

### Symptom
- C++/mobile/ONNX or serving setup fails.
- The build scripts expect tooling or artifacts that are missing.

### Likely causes
- The wrong deployment path was chosen for the model or platform.
- A platform-specific dependency or model artifact is missing.

### Recovery
- Re-read the deployment reference and narrow to the correct path.
- Treat `deploy/` scripts and `test_tipc/` entries as evidence for the supported path, not as always-runnable helpers.

## Long-running job hazards

### Symptom
- The job takes a long time or consumes more resources than expected.

### Likely causes
- Training, export, or TIPC runs are naturally expensive.
- The selected configuration is broader than the immediate user need.

### Recovery
- Do not claim success from a config parse alone.
- Keep the safe config-inspection script separate from the real training/export/deployment run.
