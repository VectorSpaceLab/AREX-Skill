---
name: vision-validation
description: "Wrap image data in VisionData, adapt loaders to BatchOutputFormat,
  run vision suites, and debug vision-format and backend issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# vision-validation

Use this sub-skill for Deepchecks Vision tasks involving:

- `VisionData` construction for image classification, object detection, semantic segmentation, or image-only work
- `BatchOutputFormat` adapters for PyTorch, TensorFlow, or custom iterables
- vision suites and checks
- custom vision properties and scorers
- torch / torchvision / image-format troubleshooting

## Route elsewhere

- Tabular `Dataset` workflows → [tabular-validation](../tabular-validation/SKILL.md)
- NLP `TextData` workflows → [nlp-validation](../nlp-validation/SKILL.md)
- Result saving, JSON/HTML export, or CI gating → [results-and-integrations](../results-and-integrations/SKILL.md)

## Start here

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/deepchecks_vision_smoke.py)

## Keep in scope

- Prefer CPU-safe, local-only examples.
- Keep EuroSAT, COCO, DETR, and Hugging Face downloads reference-only; do not make them runtime requirements here.
- General install/import problems belong in the root deepchecks troubleshooting guide, not in this sub-skill.
- Use `task_type='other'` only for image-only checks or custom formats that do not fit the built-in label/prediction shapes.
