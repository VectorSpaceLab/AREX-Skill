# Example catalog

This catalog summarizes the bundled PyTorch example workflows. `tiny_spacenet` is the minimal quickstart; the remaining entries are the example-harness keys used by the command printer.

| Example | Task | What it demonstrates | Key knobs | Default data mode | Typical outputs |
| --- | --- | --- | --- | --- | --- |
| `tiny_spacenet` | Semantic segmentation smoke test | Minimal one-train-scene, one-val-scene quickstart | `SemanticSegmentationGeoDataConfig`, `Backbone.resnet50`, one epoch | Scene-based (`GeoDataConfig`) | `train/`, `eval/`, `bundle/model-bundle.zip` |
| `spacenet-rio-cc` | Chip classification | Buildings over Rio AOI with a processed CSV and crop path | `nochip`, `external_model`, `external_loss`, `test` | Scene-based by default (`GeoDataConfig`) | `train/dataloaders/`, `eval/`, `predict/` |
| `spacenet-vegas-buildings-ss` | Semantic segmentation | SpaceNet Vegas buildings segmentation | `target=buildings`, `nochip`, `root_uri` | Scene-based (`GeoDataConfig`) | `predict/vector_outputs/`, `eval/` |
| `spacenet-vegas-roads-ss` | Semantic segmentation | SpaceNet Vegas roads segmentation | `target=roads`, `nochip`, `root_uri` | Scene-based (`GeoDataConfig`) | `predict/vector_outputs/`, `eval/` |
| `isprs-potsdam-ss` | Semantic segmentation | Multiband Potsdam segmentation with optional augmentation | `multiband`, `augment`, `allow_streaming`, `external_model` | Scene-based or chip-based | `train/valid_preds.png`, `predict/` |
| `cowc-potsdam-od` | Object detection | Car detection over Potsdam with an external detector example | `multiband`, `external_model`, `nochip` | Scene-based or chip-based | `predict/labels.tif`, `predict/vector_outputs/` |
| `xview-od` | Object detection | Vehicle detection using notebook-generated processed labels | `processed_uri`, `nochip`, `test` | Scene-based by default (`GeoDataConfig`) | `train/`, `eval/`, `bundle/model-bundle.zip` |

## Guidance by example family

- Use `spacenet-rio-cc` when you need the cleanest chip-classification path and want to compare built-in and external-model settings.
- Use `spacenet-vegas-buildings-ss` or `spacenet-vegas-roads-ss` when you want a direct semantic-segmentation example with a simple `target` override.
- Use `isprs-potsdam-ss` when you need the multiband and augmentation path.
- Use `cowc-potsdam-od` when you need an external-object-detection example.
- Use `xview-od` when you want a full detection workflow that depends on processed notebook output.

## Command printer connection

The bundled script in `scripts/list_example_commands.py` knows the six harness keys above and prints safe `rastervision run` commands for local or remote execution without running them.
