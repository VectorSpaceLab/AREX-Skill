# Prediction Troubleshooting

## Purpose

Use this reference when prediction, the demo server, or the Python API fails on
inputs, checkpoints, ffmpeg, or class-filter options.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Neither checkpoint not config specified, assuming \`accurate\`.` | The CLI fell back to the default checkpoint alias | Pass `--checkpoint` or `--config` explicitly if you want a different model. |
| `Checkpoint not found` | The selected checkpoint alias or id is missing from the local index | Route to checkpoints and refresh or download the checkpoint first. |
| `Only one of \`only-class\` or \`ignore-class\` may be specified.` | Conflicting class-filter flags | Use one filter mode at a time. |
| `No files to predict found. Accepted formats are ...` | None of the provided paths had a supported image or video extension | Verify the input files and extensions. |
| `Input ... not found, skipping.` | A path is missing or points to a nonexistent file | Fix the path or point the CLI at an existing directory. |
| `Please install ffmpeg before making video predictions.` | FFmpeg is missing from the system | Install FFmpeg if you want annotated video output. |
| `Video not being saved. Note that for the time being, no JSON output is being generated.` | A video was predicted without `--save-media-to` | Add `--save-media-to` if you need the annotated video artifact. |
| `Model type '...' not supported` | The config resolved to a model family other than Faster R-CNN or SSD | Update the config or route back to training/configuration. |
| `Missing image` or `Incompatible file type` from the server | The demo server received no file or a non-image upload | POST an image in the `image` field. |
| The API returns fewer objects than expected | The `total` query parameter or `--max-detections` cap is limiting the result | Increase the cap or remove the limit. |

## Recovery workflow

1. Run `python scripts/check_prediction_inputs.py ...` on the same paths.
2. If the checker reports missing checkpoint access, route to checkpoints.
3. If the checker reports a filter conflict, simplify the CLI flags.
4. If the issue is the model family or config, route to training.
5. If the issue is a bad media layout, fix the file set and rerun prediction.

## Notes

- Image inputs can be predicted without FFmpeg.
- Video inputs need FFmpeg only when you want saved annotated video output.
- The demo web app is intentionally lightweight and is not a production serving
  stack.
