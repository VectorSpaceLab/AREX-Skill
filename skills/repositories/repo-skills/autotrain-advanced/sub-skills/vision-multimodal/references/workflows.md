# Vision and multimodal workflows

## Command and alias map

| Workflow | CLI/config/app surface | Notes |
| --- | --- | --- |
| image classification | `autotrain image-classification`, `image-classification` YAML/app key | Image-folder class layout. |
| image regression / scoring | `autotrain image-regression`, `image-regression`, `image-scoring` | Image folder plus `metadata.jsonl` with numeric target. |
| object detection | `autotrain object-detection`, `object-detection`, `image-object-detection` | Image folder plus detection metadata. |
| VLM captioning/VQA | `vlm:captioning`, `vlm:vqa` in app/API/config | Not a top-level CLI command. |

## Safe command inspection

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py image-classification --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py image-regression --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py object-detection --help
```

If a user asks for `autotrain vlm --help`, explain that the command is not registered and inspect app/API parameters instead.

## Config validation

```bash
python skills/disco/autotrain-advanced/scripts/validate_config.py configs/vlm/<file>.yml
python skills/disco/autotrain-advanced/scripts/validate_config.py configs/object_detection/<file>.yml
```

Then verify:

- task alias resolves to the expected family;
- `base_model` matches the task type;
- `data.path` points to a local folder or accessible Hub dataset;
- image metadata columns match `data.column_mapping`;
- backend credentials are available when not using local execution.

## Local folder validation

```bash
python skills/disco/autotrain-advanced/sub-skills/vision-multimodal/scripts/validate_vision_data.py \
  --task image-classification \
  path/to/train_dir

python skills/disco/autotrain-advanced/sub-skills/vision-multimodal/scripts/validate_vision_data.py \
  --task object-detection \
  path/to/train_dir

python skills/disco/autotrain-advanced/sub-skills/vision-multimodal/scripts/validate_vision_data.py \
  --task vlm:vqa \
  --text-column answer \
  --prompt-text-column question \
  path/to/train_dir
```

## Launch pattern

Typical task-specific CLI launch:

```bash
autotrain image-classification --train --project-name img-run --data-path data/images --model google/vit-base-patch16-224 --backend local
```

Typical config launch:

```bash
autotrain --config path/to/vision.yml
```

Use the app/API backend sub-skill when the workflow depends on UI uploads, hosted Spaces, endpoints, NGC, NVCF, job state, or logs.
