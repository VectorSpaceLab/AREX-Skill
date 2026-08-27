---
name: "train-eval"
description: "Routes AdelaiDet config selection, training, evaluation,
  Detectron2 launch flags, checkpoints, and model-family run workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# train-eval

Use this sub-skill when a task asks how to train, evaluate, resume, benchmark, debug a config, or launch an AdelaiDet model family through the repository's Detectron2-style training workflow.

## Use this route for

- Selecting a config family for FCOS, BlendMask, CondInst, BoxInst, SOLOv2, MEInst, FCPose, DenseCL, or non-text detection/segmentation tasks.
- Building safe AdelaiDet training/evaluation commands with config overrides.
- Running `--eval-only`, `--resume`, distributed launch flags, or checkpoint-backed evaluation.
- Understanding output directories, dataset names, solver/batch overrides, and `MODEL.WEIGHTS` behavior.
- Diagnosing model registry/config errors after installation is already healthy.

## Do not use this route for

- Install/build/import failures. Use `../setup-build/SKILL.md` first.
- Text spotting lexicons/dictionaries/evaluation. Use `../text-spotting/SKILL.md`.
- Dataset conversion or semantic mask generation. Use `../data-prep/SKILL.md`.
- Demo visualization only. Use `../demo-visualize/SKILL.md`.
- Checkpoint key conversion or ONNX export. Use `../export-convert/SKILL.md`.

## Read first

- `references/config-selection.md` to choose a model/config family.
- `references/train-eval-workflows.md` for launch patterns, flags, and outputs.
- `../../references/model-overview.md` for package-wide model routing.
- `../../references/api-reference.md` for verified config and registry surfaces.

## Skill-owned scripts

- `scripts/run_train_eval.py` — validates common paths and builds/runs an AdelaiDet training or evaluation command. Use `--dry-run` before expensive jobs.

## Typical workflow

1. Confirm setup:

   ```bash
   python ../../scripts/check_install.py --cuda-ops
   ```

2. Choose the config family and config YAML.
3. Confirm datasets are registered and available; switch to `data-prep` if not.
4. Dry-run the launch:

   ```bash
   python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
     --config configs/FCOS-Detection/R_50_1x.yaml --num-gpus 1 --dry-run
   ```

5. Add `--eval-only --model-weights /path/to/model.pth` for evaluation-only runs, or `--resume` for continuation.
6. Inspect `OUTPUT_DIR`, logs, metrics, checkpoints, and evaluator output.

## Decision points

- If the task names BAText/ABCNet or text recognition, load `text-spotting` before finalizing training flags.
- If the config references generated semantic masks, PIC/LVIS/COCO conversions, or MEInst components, load `data-prep` before launch.
- If checkpoint keys mismatch, switch to `export-convert` for conversion utilities.
- If `No object named ... in registry` appears, verify setup/import first, then check config family/key spelling.
