# FCOS ONNX Workflows

## Export workflow

The FCOS export path builds the configured detector, loads `MODEL.WEIGHT`, then exports a sequential module containing the model backbone and FCOS/RPN head. It is intended for FCOS detector configs, not arbitrary Faster/Mask R-CNN configs.

Command shape:

```bash
python onnx_export_entry.py --config-file configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --output fcos.onnx MODEL.WEIGHT FCOS_imprv_R_50_FPN_1x.pth
```

Use the bundled builder to produce the command safely:

```bash
python sub-skills/onnx-export/scripts/build_onnx_export_command.py --config-file configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --weights FCOS_imprv_R_50_FPN_1x.pth --output fcos.onnx
```

## ONNX test workflow

The ONNX test path loads an ONNX file with a Caffe2 backend, converts ONNX outputs back to PyTorch tensors, computes FCOS locations, uses FCOS post-processing, and runs the normal inference/evaluation loop. It forces `DATALOADER.NUM_WORKERS = 0`.

This is an environment-heavy workflow: it needs ONNX, Caffe2 backend support, the FCOS package, dataset layout, config, and enough memory for the configured input size.

## OOM mitigation

If ONNX testing runs out of memory, lower `INPUT.MIN_SIZE_TEST` and keep `TEST.IMS_PER_BATCH 1`. The documented test notes recommend reducing input size for memory pressure.
