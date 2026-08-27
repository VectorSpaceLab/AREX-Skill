# CLI and Registry Troubleshooting

Use this when an `autodistill` command fails before labeling, selects the wrong model, prompts unexpectedly, or reaches credential/training side effects.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Ontologies must be valid JSON.` | Shell quoting broke the `--ontology` JSON string | Validate with `autodistill_cli_smoke.py --ontology-json ...`; wrap JSON in single quotes in POSIX shells. |
| `No ontology provided.` | `--ontology` parsed as `{}` or missing | Provide at least one prompt-to-class mapping. |
| `Module <name> not found` | Alias is not in the core registry | Run `inspect_model_registry.py`; choose one of the registered aliases or install/use a custom plugin programmatically. |
| CLI asks to install a plugin | Selected base/target plugin is not importable | Stop and confirm package, hardware, download, and license requirements before answering yes. |
| Noninteractive install fails | Registry builds `pip install autodistill_<alias>` and the distribution may be hyphenated or absent | Install the documented plugin distribution explicitly, then rerun with `-y false`. |
| `--model_type classification` or `segmentation` is rejected | Source snapshot has `SUPPORTED_MODEL_TYPES = ['detection', 'segmentationclassification']` | Use detection CLI only, use programmatic classification APIs, or refresh/fix the repo. |
| Dataset format rejected | `--dataset_format` must be one of `voc`, `yolov5`, `yolov8` | Choose a supported format for Roboflow upload or disable upload. |
| Roboflow login or upload errors | `--upload-to-roboflow true` needs credentials, network, workspace/project permissions | Disable upload for local dry runs; obtain credentials and explicit destination approval for upload. |
| Command starts downloading weights or training unexpectedly | Full CLI path imports plugins, labels data, loads target, and trains | Use `--test true` for base-model-only inference, or avoid full CLI and run safe smoke scripts first. |
| Boolean options seem ignored | Options are boolean-valued Click options in this snapshot | Pass explicit values: `--test true`, `--upload-to-roboflow false`, `-y false`. |

## Safe Debug Order

1. Run `autodistill_cli_smoke.py` to verify help output and ontology JSON.
2. Run `inspect_model_registry.py --check-installed` to see which plugin modules are importable without installing anything.
3. Verify the selected plugin package with a minimal import or single-image prediction.
4. Run CLI with `--test true` on a tiny folder if plugin inference is approved.
5. Run full labeling/training only after output paths, training time, backend, and credentials are approved.
