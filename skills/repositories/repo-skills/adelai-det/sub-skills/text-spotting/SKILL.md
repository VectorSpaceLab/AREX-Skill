---
name: "text-spotting"
description: "Guides AdelaiDet BAText/ABCNet text spotting, BezierAlign, text
  datasets, dictionaries, lexicons, and TextEvaluator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# text-spotting

Use this sub-skill when a task names BAText, ABCNet, BezierAlign, scene text, text spotting, OCR recognition, lexicons, dictionaries, text evaluation, or Bezier control-point annotations in AdelaiDet.

## Use this route for

- Choosing and editing BAText/ABCNet configs.
- Preparing text datasets and Bezier/control-point annotations.
- Understanding `BezierAlign`, `TextEvaluator`, custom dictionaries, and lexicons.
- Running text-model demos after setup succeeds.
- Debugging missing recognized strings, evaluator failures, rapidfuzz issues, or text visualization problems.

## Do not use this route for

- General installation and CUDA extension failures. Use `../setup-build/SKILL.md`.
- Non-text FCOS/BlendMask/CondInst training. Use `../train-eval/SKILL.md`.
- General COCO/PIC/LVIS conversion unrelated to text. Use `../data-prep/SKILL.md`.
- Checkpoint/ONNX conversion. Use `../export-convert/SKILL.md`.

## Read first

- `references/text-workflows.md` for BAText/ABCNet config, training, demo, and evaluation flow.
- `references/text-data-and-eval.md` for annotation fields, dictionaries, lexicons, and evaluator caveats.
- `../../references/api-reference.md` for verified BezierAlign/TextEvaluator surfaces.

## Typical workflow

1. Confirm setup with CUDA ops:

   ```bash
   python ../../scripts/check_install.py --cuda-ops
   ```

2. Choose a `configs/BAText/` YAML and inspect `MODEL.BATEXT` keys.
3. Validate text dataset annotations through `data-prep` if files are custom.
4. For training/eval, use `train-eval` launch wrappers and add text-specific overrides.
5. For visualization, use `demo-visualize` wrappers with the text config/weights.
6. Interpret recognition/evaluation results here, not in generic detection routes.

## Decision points

- **`rapidfuzz.string_metric` error:** pin `rapidfuzz<3` in setup.
- **BezierAlign op failure:** return to `setup-build`; text pooling depends on `adet._C`.
- **Boxes draw but text is blank/wrong:** check dictionary/lexicon config and annotation transcription fields.
- **Dataset lacks Bezier points:** route to `data-prep`; box-only COCO annotations are insufficient for text recognition.
- **Evaluation protocol disagreement:** identify the target benchmark lexicon/protocol before comparing numbers.
