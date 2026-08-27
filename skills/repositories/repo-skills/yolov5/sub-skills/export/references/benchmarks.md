# Benchmarks

`benchmarks.py` compares YOLOv5 formats and may export models as part of the process. It is not a lightweight command; treat it as a deployment-format validation workflow.

## Common parser flags

The inspected benchmark CLI includes `--weights`, `--imgsz`, `--batch-size`, `--data`, `--device`, `--half`, `--test`, `--pt-only`, and `--hard-fail`.

## Guidance

- Use a small checkpoint and small image size for preliminary checks.
- Understand whether the benchmark should compare PyTorch only or exported formats as well.
- Use `--pt-only` when you only want the PyTorch baseline behavior.
- `--test` often implies validation-style behavior and may depend on datasets or outputs.
- Benchmarks can download models, export artifacts, and call validation; do not run them as a casual smoke check.

## Planning checklist

1. Choose the checkpoint family.
2. Choose whether the task is export comparison or PyTorch baseline only.
3. Confirm optional backend packages before you run.
4. Confirm the dataset and device.
5. Confirm where export artifacts will be written.
