# Package API and Checkpoint Troubleshooting

## Import and API issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `prismatic` imports, but a submodule import fails | Missing optional dependency group | Install the workflow-specific dependencies: RLDS paths need TensorFlow/TFDS/dlimp; serving paths need FastAPI and serialization packages; conversion paths need `timm`, `transformers`, and the HF stack. |
| `load()` downloads instead of using a local checkpoint | The path was not treated as a local directory or a registered model id was passed | Pass the exact local directory or explicit model id you want to load. |
| `load_vla()` fails with missing statistics | `dataset_statistics.json` is absent or the checkpoint path is not the run directory layout it expects | Keep the statistics file beside the run checkpoint and pass the actual `.pt` file under `checkpoints/`. |
| `ActionTokenizer` raises `NotImplementedError` for `use_extra=True` | Tokenizer is not Qwen2-style | Disable `use_extra` or switch to a supported Qwen2 tokenizer. |
| Action dimensions look wrong at runtime | Robot platform detection chose the wrong constants | Include the intended platform word in the launch command text or inspect `prismatic.vla.constants.ROBOT_PLATFORM` before using the model. |

## Checkpoint and conversion issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `dataset_statistics.json` is missing | The checkpoint is incomplete or already converted to a non-native HF bundle | Restore the statistics file from the training output or use a checkpoint that preserves native VLA files. |
| `lora_adapter/` is missing | The checkpoint is already merged or was not produced by the LoRA fine-tuning flow | Run the merge utility only on adapter checkpoints. |
| HF conversion reports a key mismatch | The base VLM, fused-vision setting, or Pro/minivision mapping does not match the checkpoint | Match the converter to the exact model family and config. |
| Merge or conversion runs out of memory | The base model and adapter together exceed available memory | Use a larger device or run the merge on a machine with more headroom. |
| HF export loads locally but not through AutoClasses | The export bundle is missing config/processor/tokenizer assets or the remote-code files are stale | Rebuild the export bundle and re-check the files with the layout checker. |

## What the bundled checker catches

The checker verifies:

- the checkpoint root exists
- `config.json` exists and parses
- `dataset_statistics.json` exists when requested
- `lora_adapter/` exists when requested
- HF-style config assets are present when requested

It does not read model weights, run inference, or validate numeric quality.
