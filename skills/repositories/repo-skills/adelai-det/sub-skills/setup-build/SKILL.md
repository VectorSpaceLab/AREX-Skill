---
name: "setup-build"
description: "Guides legacy-compatible AdelaiDet installation,
  Detectron2/PyTorch/CUDA version selection, editable extension builds, and
  runtime smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# setup-build

Use this sub-skill when a task involves installing AdelaiDet, selecting PyTorch/Detectron2/CUDA versions, building `adet._C`, checking custom operators, or diagnosing import/build failures.

## Use this route for

- Creating a fresh environment for AdelaiDet.
- Choosing a Detectron2 wheel that matches PyTorch and CUDA.
- Building `AdelaiDet` editable from source.
- Verifying `adet.config.get_cfg`, Detectron2 registries, `adet._C`, BezierAlign, DefROIAlign, and multi-label NMS.
- Fixing build failures such as missing torch in build isolation, missing CUDA headers, missing THC headers, Pillow/rapidfuzz/OpenCV incompatibilities, or CUDA architecture problems.

## Do not use this route for

- Choosing a model config after installation succeeds. Use `../train-eval/SKILL.md`.
- Demo commands with an already working install. Use `../demo-visualize/SKILL.md`.
- Dataset annotation conversion. Use `../data-prep/SKILL.md`.
- ONNX and checkpoint conversion. Use `../export-convert/SKILL.md`.

## Read first

- `references/setup-build.md` for the known-good install recipe and version pins.
- `references/runtime-checks.md` for what each smoke check proves.
- `../../references/compatibility.md` for package-version rationale.
- `../../references/troubleshooting.md` for cross-cutting error fixes.

## Skill-owned scripts

- `../../scripts/check_install.py` — package/config/registry/extension smoke check, with optional `--cuda-ops`.

## Standard workflow

1. Create the compatible Python/PyTorch/CUDA/Detectron2 environment described in `references/setup-build.md`.
2. Install AdelaiDet with `python -m pip install --no-build-isolation -e <checkout>`.
3. Pin compatibility fixes: `Pillow<10`, `rapidfuzz<3`, NumPy `1.23.x`, and OpenCV headless `4.8.x`.
4. Run:

   ```bash
   python ../../scripts/check_install.py --cuda-ops
   ```

5. If `--cuda-ops` fails, do not start training or inference; fix setup first or explicitly narrow the task to import/config-only analysis.

## Decision points

- **Need unmodified CUDA extension?** Use PyTorch 1.10.x + CUDA 11.3. PyTorch 2.x is not the default.
- **No GPU available?** You may perform import/config-only checks without `--cuda-ops`, but record that DefROIAlign and native `_C.ml_nms` are not validated.
- **Need ONNX/TensorRT/NCNN?** First prove the base AdelaiDet install, then switch to `export-convert` for optional deployment runtimes.

## Success signal

A healthy CUDA-capable environment reports:

- `import adet` succeeds.
- `adet._C` exposes BezierAlign, DefROIAlign, and `ml_nms` symbols.
- `scripts/check_install.py --cuda-ops` exits 0.
- CLI help for training/demo/visualization/export can import all required modules.
