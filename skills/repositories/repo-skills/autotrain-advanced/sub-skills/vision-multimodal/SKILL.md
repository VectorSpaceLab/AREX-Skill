---
name: vision-multimodal
description: "Operate AutoTrain Advanced image classification, image regression,
  object detection, and VLM app/API/config workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain vision and multimodal workflows

Use this sub-skill for image classification, image regression/scoring, object detection, and VLM dataset/task flows.

## Supported entry points

- `autotrain image-classification --help`
- `autotrain image-regression --help`
- `autotrain object-detection --help`
- YAML aliases: `image-classification`, `image-regression`, `image-scoring`, `object-detection`, `image-object-detection`, `vlm:captioning`, `vlm:vqa`
- App/API task keys: `image-classification`, `image-regression`, `image-object-detection`, `vlm:captioning`, `vlm:vqa`

Important: there is no top-level `autotrain vlm` command in this checkout. Route VLM through the app/API/config flow.

## Data-layout summary

| Task | Local layout |
| --- | --- |
| image classification | directory with at least two class subfolders; each class folder has at least five jpg/jpeg/png files and no extra files/subfolders |
| image regression | directory with at least five images plus `metadata.jsonl` containing `file_name` and `target` |
| object detection | directory with at least five images plus `metadata.jsonl` containing `file_name` and `objects` |
| VLM | directory with at least five images plus `metadata.jsonl` containing `file_name` and all mapped text/prompt columns |

Use `scripts/validate_vision_data.py` for bounded local layout checks.

## Safe validation sequence

1. Inspect relevant CLI help with the root `inspect_cli.py` helper.
2. Validate YAML with the root `validate_config.py` helper.
3. Validate local image folders/metadata with `scripts/validate_vision_data.py`.
4. If VLM or UI/API parameters are involved, use `../app-backends/` to inspect app/API task params and backend auth.
5. Launch only after data layout, model id, task alias, backend, and Hub credentials are explicit.

## References

- `references/workflows.md` — route patterns and launch/check examples.
- `references/data-formats.md` — local folder and metadata schemas.
- `references/troubleshooting.md` — image file counts, metadata parsing, VLM route, and backend issues.
