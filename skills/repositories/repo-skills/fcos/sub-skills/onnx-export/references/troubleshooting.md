# ONNX Export Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `This script is only tested for the detector FCOS` | Config does not set `MODEL.FCOS_ON` for FCOS. | Choose a FCOS config from the config catalog. |
| Missing `onnx` or Caffe2 backend | Optional ONNX test dependencies are not installed or deprecated. | Install only if the user approves; otherwise validate command construction and output contract. |
| Missing weights | Export loads `cfg.MODEL.WEIGHT`. | Download or provide a local weight file explicitly before running export. |
| CUDA/CPU device mismatch | Config `MODEL.DEVICE` and runtime hardware disagree. | Override `MODEL.DEVICE cpu` for CPU export tests or verify CUDA first. |
| OOM during export/test | Dummy input or test input too large. | Lower `INPUT.MIN_SIZE_TEST`, use `TEST.IMS_PER_BATCH 1`, or run on a larger GPU. |
| Unexpected output names/order | Consumer assumes end-to-end detector outputs. | Use `output-contract.md`; outputs are per-FPN logits/bbox_reg/centerness, not final boxes. |
