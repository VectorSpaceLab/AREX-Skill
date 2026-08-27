# Vision and VLM troubleshooting

## Folder layout failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Image classification says the path needs at least two subfolders | Training directory is not class-folder style | Create one subfolder per class. |
| A class folder needs at least five images | AutoTrain preprocessor enforces a minimum image count | Add images or use a larger sample. |
| A class folder should not contain other files | Non-image files are inside a class folder | Move labels/metadata elsewhere; class folders should contain only images. |
| Validation classes do not match train classes | Train/validation directories have different subfolder names | Align class folders before preprocessing. |

## Metadata failures

- Image regression requires `metadata.jsonl` with `file_name` and `target`.
- Object detection requires `metadata.jsonl` with `file_name` and `objects`.
- VLM requires `metadata.jsonl` with `file_name` and every mapped text/prompt column.
- Make sure `file_name` values point to image files present in the same directory.
- Keep extensions to jpg/jpeg/png variants accepted by the source preprocessor.

## VLM route failures

- `autotrain vlm` is not registered. Use YAML/app/API task keys such as `vlm:captioning` or `vlm:vqa`.
- Use `app-backends` when VLM is being launched through the UI or API and the issue involves params, uploads, backend auth, jobs, or logs.

## Backend and model issues

- Image and VLM training can download models and datasets; do not use full training as a cheap smoke test.
- Start with config parsing and local data validation.
- Hosted backends require Hub-accessible data/model artifacts and credentials.
- If object detection metadata validates but training fails later, inspect the exact `objects` annotation shape expected by the model/trainer.

## Minimal recovery checklist

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py image-classification --help
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/vision.yml
python skills/disco/autotrain-advanced/sub-skills/vision-multimodal/scripts/validate_vision_data.py --task <task> path/to/train_dir
```
