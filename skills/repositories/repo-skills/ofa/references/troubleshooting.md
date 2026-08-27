# Troubleshooting

## Read this first

This page covers OFA problems that can block many workflows: install/import issues, CUDA readiness, Java for COCO caption evaluation, missing datasets/checkpoints, and command-shape mistakes. For task-specific issues, read the nearest sub-skill troubleshooting file after this one.

## Import or CLI help fails

**Symptoms**

- `ImportError` from `train.py` or `evaluate.py`
- `cannot import name 'metrics' from 'fairseq'`
- Fairseq modules resolving to the wrong installed package
- `train.py --help` or `evaluate.py --help` crashing before printing usage

**Likely causes**

- The repo root is not visible on `PYTHONPATH`.
- The bundled `fairseq/` fork is not the first Fairseq import target.
- The environment is missing the repo requirements.

**What to do**

1. Run `scripts/check_ofa_environment.py --check-clis`.
2. Make sure the repo root and bundled `fairseq/` fork are visible to Python.
3. Reinstall the repo requirements if the helper reports missing packages.

**When to stop**

- If the helper reports a missing optional dependency or a backend that the workflow truly requires, fix that dependency before continuing.

## CUDA or backend mismatch

**Symptoms**

- The workflow is documented as GPU-based, but `torch.cuda.is_available()` is false.
- The command appears to run, but model execution is obviously CPU-only and too slow.
- A task command crashes as soon as it tries to move tensors or models to CUDA.

**Likely causes**

- No CUDA-capable PyTorch build is installed.
- The host has no visible GPUs.
- The workflow requires GPU assets or memory that the current environment cannot supply.

**What to do**

- Use `scripts/check_ofa_environment.py --require-cuda` to confirm readiness.
- Treat CPU-only checks as useful for parser/import validation only.
- Do not claim a task is validated on CPU if the workflow is a genuine GPU workflow.

## COCO caption evaluation complains about Java or SPICE

**Symptoms**

- `pycocoevalcap` raises a Java-related error.
- Caption evaluation prints metrics except SPICE, or fails inside the metric helper.

**Likely causes**

- Java 1.8 is not installed.
- The COCO evaluation stack is incomplete.

**What to do**

- Use `sub-skills/vision-language-tasks/scripts/coco_caption_eval.py` only when the dependency stack is available.
- If Java is unavailable, stop short of full SPICE evaluation and document the limitation.

## Missing datasets or checkpoints

**Symptoms**

- The task command fails with `No such file or directory`.
- The model loader cannot find a checkpoint.
- A TSV or manifest validator fails because the file exists but the row shape is wrong.

**Likely causes**

- The repo's datasets and checkpoints are not downloaded.
- A path in the launch command still points at a placeholder.
- The input layout does not match the task's selected columns.

**What to do**

- Validate the input layout first with the relevant sub-skill helper.
- Confirm that the dataset/checkpoint folder structure matches the task family.
- Replace placeholder paths only after the validator passes.

## Common command-shape mistakes

- Forgetting `--user-dir=ofa_module`.
- Passing the wrong `--task` for a workflow family.
- Copying a distributed script with the wrong `MASTER_PORT` or GPU list.
- Using a caption/VQA `selected_cols` layout for RefCOCO, OCR, or pretraining.
- Confusing beam-search and all-candidate evaluation in VQA.

## Safe recovery loop

1. Run the bundled environment checker.
2. Validate the input file or manifest.
3. Render the command with `scripts/render_ofa_command.py`.
4. Read the nearest sub-skill troubleshooting page for the workflow family.
5. Only then launch a heavy GPU job.
