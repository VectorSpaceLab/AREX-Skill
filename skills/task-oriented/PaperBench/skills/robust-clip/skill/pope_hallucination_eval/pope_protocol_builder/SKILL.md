---
name: pope_protocol_builder
description: Build POPE polling-question datasets from image object annotations and prompt templates.
---

# POPE Protocol Builder

Use this skill when you need to turn annotation-style object records into POPE yes/no polling questions for object hallucination evaluation. It should be used before model inference and before answer evaluation.

Do not use this skill to choose metric thresholds, run LVLM inference, or score answers. It owns question construction and delegates absent-object selection to POPE negative sampling logic.

## Inputs

- Records with `image` and `objects` fields.
- `sample_num`, the number of positive object probes per image.
- Negative strategy: `random`, `popular`, or `adversarial`.
- Prompt template containing one `{}` placeholder, such as `Is there a {} in the image?`.
- Optional random seed.

## Outputs

- Question records with `question_id`, `image`, `text`, `object`, `label`, and `strategy`.
- A balanced set of positive and negative probes for every retained image.
- Optional JSONL file for downstream LVLM answering.

## Workflow

1. Normalize and filter records so only images with at least `sample_num` objects are retained.
2. For each retained image, select `sample_num` positive objects from that image.
3. Emit a `yes` question for each positive object.
4. Call the negative sampler with the selected strategy, current image objects, and per-image history.
5. Emit a matched `no` question for each selected absent object.
6. Keep question IDs monotonic and preserve enough metadata for audit logs.

## Validation

Run:

```bash
python scripts/pope_protocol_builder.py --self-test
python tests/test_protocol_builder.py
```

The tests check label balance, absent-object constraints, question IDs, and template text.

## Limitations

The skill requires object annotations or segmentation outputs. It does not inspect images, run SEEM, or infer object lists.