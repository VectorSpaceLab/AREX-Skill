# Install and Environment

## Purpose

Read this before using the D-FINE repo skill in a fresh checkout. It explains the public install paths, which optional backend packages belong to which workflows, and the smallest smoke check that proves the checkout is usable.

## Baseline install

D-FINE is source-driven and does not expose a packaging metadata file in this checkout. The public runtime path is therefore a direct checkout install:

```bash
pip install -r requirements.txt
```

That baseline is enough for the core Python modules, YAML config loading, and the training/inspection workflows covered by this skill.

## Optional workflow-specific installs

Install only what the selected workflow needs:

- **Inference / export**: `pip install -r tools/inference/requirements.txt`
- **Benchmarking**: `pip install -r tools/benchmark/requirements.txt`
- **ONNX export**: `pip install onnx onnxsim`
- **FiftyOne visualization**: `pip install fiftyone`
- **Inspection fallback**: `pip install matplotlib` if solver/validator imports fail during architecture or config inspection

Do not install TensorRT, OpenVINO, or pycuda unless the user explicitly needs those backends.

## Backend guidance

- CPU import and config inspection are enough for the core training/config/architecture routes.
- CUDA is only needed for actual GPU training, TensorRT inference, or GPU-bound benchmark workflows.
- ONNX Runtime and OpenVINO are optional deployment paths; keep them out of the minimum install unless the user asked for them.
- TensorRT and pycuda are highly environment-specific and should be treated as optional backend prerequisites, not default dependencies.

## Smoke check

Run the bundled probe from the checkout root after installation:

```bash
python scripts/dfine_environment_probe.py --repo-root . --config configs/dfine/dfine_hgnetv2_n_coco.yml --build-model
```

The probe should:

- import the D-FINE modules needed for registry-based construction,
- load the YAML config,
- build the smallest COCO D-FINE model with pretrained backbone lookup disabled by default,
- print the model class and parameter count.

If the user wants a stronger check, add `--dummy-forward`, but only when the machine has enough RAM and the selected device/backend is available.

## Common install mistakes

- Using the wrong config family for the checkpoint or dataset.
- Skipping the optional `onnx` / `onnxsim` packages before export.
- Expecting TensorRT or OpenVINO helpers to work without their runtime packages.
- Treating a CPU-only setup as proof that CUDA/TensorRT workflows are ready.
