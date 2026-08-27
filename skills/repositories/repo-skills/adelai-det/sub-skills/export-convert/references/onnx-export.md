# ONNX export and optional deployment runtimes

AdelaiDet's source ONNX exporter builds a model from a config, loads `MODEL.WEIGHTS`, patches selected forward paths to be ONNX-friendly, and calls `torch.onnx.export` on a dummy image tensor.

## Export command

Dry-run first:

```bash
python scripts/export_onnx.py --repo-root /path/to/AdelaiDet \
  --config configs/FCOS-Detection/R_50_1x.yaml \
  --weights /path/to/model.pth \
  --output output/fcos.onnx \
  --width 1088 --height 800 --dry-run
```

Run for real after setup and paths are validated:

```bash
python scripts/export_onnx.py --repo-root /path/to/AdelaiDet \
  --config configs/CondInst/MS_R_50_1x.yaml \
  --weights /path/to/model.pth \
  --output output/condinst.onnx \
  --opts MODEL.DEVICE cuda
```

The wrapper appends `MODEL.WEIGHTS <weights>` and forwards optional `--width`, `--height`, `--level`, and `--opts` to the source exporter.

## Supported model patterns

The source exporter contains patches for these patterns:

- `condinst.CondInst`
- `BlendMask`
- Detectron2 `ProposalNetwork` with FCOS proposal generator
- FCOS proposal-generator head
- CondInst `MaskBranch`

Other architectures may need code changes or custom export logic.

## Input shape

Default dummy input is `1 x 3 x 800 x 1088`. Override with `--height` and `--width` when your deployment target needs a fixed shape.

## Runtime validation

ONNX export does not prove deployment correctness. Optional validation may require:

- `onnx` checker
- ONNXRuntime
- Caffe2
- TensorRT
- Caffe
- NCNN
- onnx-simplifier
- Target-specific plugins or conversion tools

These were not part of the minimum verified install. Install and document them only for a concrete deployment task.

## Source shell scripts are reference-only

The source `onnx/pytorch-onnx-caffe-ncnn*.sh` scripts encode a conceptual path from PyTorch to ONNX to Caffe/NCNN/TensorRT, but they assume external workspaces, custom projects, model files, and hard-coded paths. Do not run them blindly. Reconstruct a safe local pipeline with explicit inputs/outputs.

## Common failures

| Symptom | Likely issue | Fix |
| --- | --- | --- |
| Config/model build fails | Setup or model-family mismatch. | Run `check_install.py --cuda-ops`; verify config family. |
| Weight load mismatch | Wrong checkpoint key naming or model architecture. | Use checkpoint utilities or correct config. |
| ONNX export unsupported op | Model path not covered by source patches. | Patch forward/export path or narrow target architecture. |
| Runtime comparison differs | Pre/postprocessing or unsupported runtime op. | Validate image normalization, shape, output names, and runtime plugin support. |
