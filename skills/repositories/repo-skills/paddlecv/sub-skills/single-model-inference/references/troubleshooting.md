# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Detection or segmentation config fails before inference | The `Inputs` edges or op order are wrong. | Compare the YAML against the model op's declared output keys. |
| The output image never appears in the output directory | `save_img` is false or the output op does not support image saving for that family. | Enable the correct output flags or inspect the output op implementation. |
| `No model found` from `list_model` | The filter terms do not match the generated model catalog. | Use shorter substring filters, such as `PP-LCNet` or `system`. |
| The input file is rejected | The input is not an image, directory, or video path. | Pass a supported image path, directory, or video file. |
| Model download errors for single-op configs | The `paddlecv://` asset is missing or the network/cache is unavailable. | Retry with access to the model cache or pre-download the asset. |

## Selection hints
- If the user is asking for OCR or a multi-stage preset, this sub-skill is probably the wrong route.
- If the user is changing operator graph wiring rather than one-model inference, hand off to `custom-ops`.
