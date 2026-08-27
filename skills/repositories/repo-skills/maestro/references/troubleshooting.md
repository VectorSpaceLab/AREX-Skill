# Maestro root troubleshooting

Use this for package-wide install, CLI, backend, credential, and output-location failures. Use model sub-skill troubleshooting when the problem is model-specific.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for a model recipe when running `maestro --help` | Only base package is installed, so optional model dependencies are missing. | Install the model extra you need, for example `pip install "maestro[qwen_2_5_vl]"`, or set `DISABLE_RECIPE_IMPORTS_WARNINGS=True` only for root CLI probing. |
| CLI does not show `florence_2`, `paligemma_2`, or `qwen_2_5_vl` | Recipe discovery failed during optional imports. | Install the relevant extra and rerun `maestro --help`; use `python scripts/maestro_cli_probe.py --include-model-help` for a safe route check. |
| `Requested device 'cuda' is not available` | The selected device string is not visible through PyTorch. | Use `device="auto"`, use `cpu` for safe inspection/formatter checks, or move to a runtime with a compatible CUDA PyTorch build. |
| QLoRA or `bitsandbytes` fails | Quantized model paths need compatible CUDA/bitsandbytes support. | Use a CUDA-capable environment, lower the model/task memory footprint, or switch to `lora`/`none` where the model sub-skill permits it. |
| `flash-attn` build fails while installing Florence extra | Compiler/CUDA/ABI mismatch for an optional acceleration dependency. | If full accelerated Florence training is required, fix the CUDA/build toolchain. For API/formatter inspection or non-accelerated experiments, install Maestro with `torch`, `transformers`, and `peft` manually and document that `flash-attn` was skipped. |
| Qwen detection formatter raises `smart_resize()` missing `factor` or signature errors | `qwen-vl-utils` version drift. | Pin `qwen-vl-utils==0.0.8` for this Maestro source version and rerun the Qwen formatter smoke. |
| `ROBOFLOW_API_KEY` error | Dataset string did not resolve to a local path and was parsed as a Roboflow identifier. | Set `ROBOFLOW_API_KEY`, use a local downloaded dataset path, or correct the dataset identifier. |
| Roboflow dataset type is unsupported | Common resolver supports Roboflow object-detection as COCO and text-image-pairs as JSONL. | Export/download a supported format or convert to the JSONL/COCO layouts described in the dataset sub-skill. |
| `Unsupported metric` | Metric name is outside Maestro's registry. | Use `edit_distance`, `bleu`, or `mean_average_precision`; route metric questions to [datasets-and-metrics](../sub-skills/datasets-and-metrics/SKILL.md). |
| Training starts but no metrics or checkpoint files are found | Training did not reach the callback/fit end, output path was unexpected, or process was interrupted. | Check the numbered run directory under the configured `output_dir`, reduce batch size/sequence length, and rerun. Checkpoints are written under `checkpoints/latest`; metric plots under `metrics/`. |
| CLI accepts a command but then raises an unbound `peft_advanced_params_dict`-style error | Current model CLI entrypoint edge case when PEFT JSON option is omitted. | Pass `--peft_advanced_params '{}'` or use the Python `train(config)` API with `peft_advanced_params=None`. |
| A safe bundled script fails to import Maestro | The runtime environment does not contain Maestro or required optional imports for that script. | Run `python scripts/check_maestro_environment.py --models all --json`, then install the missing package or choose a narrower model route. |

## Safe diagnosis sequence

From the generated Maestro skill tree:

```bash
python scripts/check_maestro_environment.py --models all --json
python scripts/maestro_cli_probe.py --include-model-help --json
python sub-skills/datasets-and-metrics/scripts/smoke_coco_vlm_adapter.py
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json
python sub-skills/qwen-2-5-vl/scripts/smoke_qwen_detection_format.py
```

These checks avoid Roboflow downloads, Hugging Face model downloads, training, destructive writes, and credentials. Passing them means the package APIs and deterministic helpers are available; it does not prove that a full model fine-tuning run will fit in memory or that remote downloads/credentials are valid.

## When to stop and ask for resources

Stop before full training or model inference when the user has not provided or approved:

- model download/network access,
- Hugging Face credentials for gated/private checkpoints,
- Roboflow credentials for dataset downloads,
- GPU/VRAM use for large VLM training,
- write location for checkpoints and metric plots,
- runtime budget for multi-epoch training.
