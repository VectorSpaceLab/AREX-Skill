---
name: "export-convert"
description: "Guides AdelaiDet checkpoint key conversion, optimizer stripping,
  FCOS/BlendMask weight migration, ONNX export, and optional deployment-runtime
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# export-convert

Use this sub-skill when a task asks to convert AdelaiDet checkpoints, rename FCOS/BlendMask keys, remove optimizer state, export an AdelaiDet model to ONNX, or reason about optional Caffe/NCNN/TensorRT deployment paths.

## Use this route for

- Migrating official FCOS weights to AdelaiDet/Detectron2 key names.
- Renaming BlendMask `centerness` keys to `ctrness`.
- Stripping checkpoint optimizer/training state for smaller inference files.
- Building safe ONNX export commands for FCOS/BlendMask/CondInst-style models.
- Explaining why source Caffe/NCNN/TensorRT shell scripts are reference-only unless external runtimes are prepared.

## Do not use this route for

- Installing or building `adet._C`. Use `../setup-build/SKILL.md`.
- Choosing training configs or launching evaluation. Use `../train-eval/SKILL.md`.
- Image/video demos from PyTorch checkpoints. Use `../demo-visualize/SKILL.md`.
- Dataset preparation. Use `../data-prep/SKILL.md`.
- Text-specific recognition/evaluation protocol. Use `../text-spotting/SKILL.md`.

## Read first

- `references/export-and-checkpoints.md` for checkpoint utility behavior.
- `references/onnx-export.md` for export constraints and optional runtime validation.
- `../../references/compatibility.md` before mixing export tools with a different PyTorch/Detectron2 stack.

## Skill-owned scripts

- `scripts/convert_fcos_weight.py` — convert official FCOS ResNet/FPN naming into AdelaiDet/Detectron2 naming.
- `scripts/rename_blendmask_weights.py` — rename BlendMask `centerness` keys to `ctrness`.
- `scripts/strip_checkpoint_optimizer.py` — save only the model state from a checkpoint.
- `scripts/export_onnx.py` — validated wrapper around the repository ONNX exporter.

## Typical workflow

1. Confirm base setup with `../../scripts/check_install.py --cuda-ops`.
2. For checkpoint key errors, run the relevant small conversion script on a copy of the checkpoint.
3. For ONNX export, dry-run first:

   ```bash
   python scripts/export_onnx.py --repo-root /path/to/AdelaiDet \
     --config configs/FCOS-Detection/R_50_1x.yaml \
     --weights /path/to/model.pth --output output/model.onnx --dry-run
   ```

4. Remove `--dry-run` only after config, weights, device, and output path are correct.
5. Validate exported ONNX with the runtime stack required by the downstream target; do not assume Caffe/NCNN/TensorRT are installed.

## Decision points

- If checkpoint loading fails during training/eval, fix key naming here then return to `train-eval`.
- If ONNX export fails at model build/config import, return to `setup-build` or `train-eval` depending on the traceback.
- If deployment asks for Caffe, NCNN, TensorRT, or ONNXRuntime comparison, treat that as an expanded environment task with external dependencies and artifacts.
