# Florence-2 troubleshooting

Use this when a Maestro Florence-2 command, Python API call, detection format conversion, or checkpoint workflow fails. For package-wide install and CLI issues, also check [root troubleshooting](../../../references/troubleshooting.md). For dataset schemas, Roboflow identifiers, and metric definitions, use [datasets-and-metrics troubleshooting](../../datasets-and-metrics/references/troubleshooting.md).

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `--optimization_strategy qlora` fails or behaves unexpectedly | Florence-2 supports `lora`, `freeze`, and `none` only. | Replace with `--optimization_strategy lora`, `freeze`, or `none`. Do not claim QLoRA support for Florence-2. |
| CLI train command raises an undefined `peft_advanced_params_dict`/similar local variable error | Current CLI edge case when `--peft_advanced_params` is omitted. | Add `--peft_advanced_params '{}'` to the CLI command, or use the Python API where `peft_advanced_params=None` is valid. |
| `--peft_advanced_params` fails JSON parsing | The CLI expects a JSON dictionary string. | Use a shell-quoted object such as `'{}'` or `'{"r": 16, "lora_alpha": 32}'`; do not pass a JSON list or unquoted shell braces. |
| `TypeError` from `peft.LoraConfig` | Custom LoRA parameters include unsupported keys or wrong value types. | Start from Maestro's defaults, override only known `LoraConfig` fields, and test with a small run. |
| Import errors for `peft`, `transformers`, `torch`, or `flash_attn` | Florence extras or accelerator-specific dependencies are missing or failed to build. | Install `maestro[florence_2]` in a model-specific environment. If `flash-attn` build fails and accelerated attention is not required, install Maestro plus `torch`, `transformers`, and `peft` manually and document that full accelerated training was not verified. |
| Hugging Face load requests remote code or fails on model files | Florence loaders call Hugging Face auto classes with `trust_remote_code=True`, model id, revision, and optional cache. | Use `model_id="microsoft/Florence-2-base-ft"`, `revision="refs/pr/20"`, set a `cache_dir` if needed, authenticate separately for private/gated models, and retry once network/cache issues are resolved. |
| `Requested device 'cuda' is not available` or similar | `Florence2Configuration` validates the requested device. | Use `device="auto"` for automatic selection or `device="cpu"` for safe API/formatter checks. Use CUDA only on a machine with compatible PyTorch/CUDA. |
| GPU out-of-memory during train or validation | Batch size, validation generation, or full model strategy is too large. | Prefer `optimization_strategy="lora"`, lower `batch_size` and `val_batch_size`, lower `max_new_tokens`, keep `num_workers` modest, and use a smaller Florence model id if appropriate. |
| COCO dataset error says formatter callbacks are missing | Manual `create_data_loaders(...)` was called on a COCO dataset without model-specific formatters. | Pass `detections_to_prefix_formatter` and `detections_to_suffix_formatter` from `maestro.trainer.models.florence_2.detection`, or call `train(...)` which wires them automatically. |
| No train/valid/test splits found | Maestro's common loader requires all three splits. | Repair the dataset structure as described by [datasets-and-metrics data formats](../../datasets-and-metrics/references/data-formats.md). |
| `Unsupported metric` | Metric string is not in Maestro's metric registry. | Use `edit_distance`, `bleu`, or `mean_average_precision`. For object detection, include `mean_average_precision` only when suffixes use the Florence detection grammar. |
| mAP stays zero or detections are empty | Generated suffixes do not match the parser grammar, class labels are unknown, or coordinates are malformed. | Run `python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json`; sanitize class names to word/space labels; ensure suffixes are `class<loc_xmin><loc_ymin><loc_xmax><loc_ymax>`. |
| Hyphenated or punctuated class names disappear during parsing | The parser pattern accepts word characters and spaces, not arbitrary punctuation. | Map labels like `traffic-light` to `traffic light` or `traffic_light` before formatting, and maintain a reversible class-name map. |
| Parsed boxes have wrong scale | `resolution_wh` did not match the image width/height used when formatting. | Always pass `(image.width, image.height)` as `resolution_wh`, not `(height, width)`. |
| Loading a saved checkpoint for inference fails | The path does not contain both saved processor files and model files, or the wrong optimization wrapper is being requested. | Load the Maestro checkpoint directory that contains `processor.save_pretrained` and `model.save_pretrained` outputs; for ordinary inference use `OptimizationStrategy.NONE`. |
| Validation logs show generated text with special tokens | Florence inference decodes with `skip_special_tokens=False`. | Post-process consistently with either the Florence processor's task post-processor or Maestro's detection parser, and keep metric parsing assumptions explicit. |

## Quick diagnostic snippets

Check CLI availability without training:

```bash
maestro florence_2 train --help
```

Check the deterministic Florence detection grammar without a model download:

```bash
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json
```

Check Python API construction without starting training:

```python
from maestro.trainer.models.florence_2.core import Florence2Configuration

config = Florence2Configuration(
    dataset="./dataset",
    optimization_strategy="lora",
    metrics=["edit_distance"],
    device="cpu",
)
print(config)
```

This validates metric names and device availability, but it does not verify dataset existence, model download, or training success.
