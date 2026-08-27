# Autodistill CLI Reference

Read this when constructing, reviewing, or debugging `autodistill` shell commands. This reference reflects the Autodistill 0.1.29 source snapshot and installed `autodistill --help` output.

## Command Shape

```bash
autodistill IMAGES [OPTIONS]
```

`IMAGES` is a path to an image folder or a single image file. A full run may label images, train a target model, and optionally upload to Roboflow.

## Verified Options

| Option | Meaning | Safe dry-run note |
|---|---|---|
| `--models BOOLEAN` | Print available model aliases from the loaded model matrix. | Safe when passed as `--models true`; exits after printing. |
| `--base TEXT` | Base model alias for labeling, default `grounding_dino`. | Requires a plugin package for full runs. |
| `--target TEXT` | Target model alias for training, default `yolov8`. | Requires a plugin package for full runs. |
| `--model_type TEXT` | Model type, documented as detection/segmentation/classification. | Source snapshot has a missing-comma bug; see caveat below. |
| `--ontology TEXT` | JSON mapping from prompt to saved class name. Required. | Validate with the bundled smoke script before running. |
| `--epochs INTEGER` | Training epochs for the target model. Default 200. | Full training can be expensive. |
| `--output TEXT` | Output directory for labeled data. Default `./dataset`. | May be overwritten or mutated by dataset writing. |
| `--upload-to-roboflow BOOLEAN` | Upload dataset and trained model to Roboflow. | Requires explicit credentials/network approval. |
| `--project_name TEXT` | Roboflow project name. | Only used on upload paths. |
| `--project_license TEXT` | Roboflow project license or `private`. | Only used on upload paths. |
| `--dataset_format TEXT` | Roboflow upload dataset format: `voc`, `yolov5`, or `yolov8`. | Validated before a full run. |
| `-y BOOLEAN` | Answer yes to install prompts. | Can trigger plugin installation; avoid unless approved. |
| `--test BOOLEAN` | Run the base model on up to 9 images and show results instead of training. | Still needs plugin inference and may download weights. |

In this Click definition, boolean options are declared with `default=False` rather than flag syntax, so use explicit values such as `--upload-to-roboflow false`, `--test true`, or `-y false`.

## Safe Command Construction

Validate the ontology string separately:

```bash
python scripts/autodistill_cli_smoke.py \
  --ontology-json '{"acoustic guitar": "guitar"}'
```

Then construct the full command only after plugin installation and backend requirements are understood:

```bash
autodistill images \
  --base grounding_dino \
  --target yolov8 \
  --model_type detection \
  --ontology '{"acoustic guitar": "guitar"}' \
  --epochs 50 \
  --output ./dataset \
  --upload-to-roboflow false \
  -y false
```

## Single Image Behavior

If `IMAGES` points to a file, the CLI labels that file's containing directory using the file's extension, predicts on the file, plots/saves an annotated frame as `result.jpg` in the current working directory, and exits before target training.

This path still needs the selected base plugin and may invoke display/image output side effects.

## Test Mode

With `--test true`, the CLI reads up to 9 files from the image directory, predicts each with the base model, plots a 3x3 grid, and exits before target loading or training. It still runs real plugin inference.

## Upload Path

With `--upload-to-roboflow true`, the CLI logs into Roboflow, validates upload-supported target model values, creates or reuses a Roboflow project, uploads the dataset, generates a version, and deploys model weights. Treat this as credentialed, networked, and externally mutating.

## Model Type Caveat

The source snapshot defines:

```python
SUPPORTED_MODEL_TYPES = ["detection", "segmentation" "classification"]
```

Python concatenates adjacent strings, so the actual value is `['detection', 'segmentationclassification']`. As a result, `--model_type segmentation` and `--model_type classification` may be rejected even though public docs mention them. For classification/segmentation workflows, prefer programmatic APIs or refresh/fix the repo before relying on the CLI.
