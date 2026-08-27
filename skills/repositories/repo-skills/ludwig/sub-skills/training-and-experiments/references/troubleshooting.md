# Training Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training cannot find a feature column | Config/data mismatch | Validate config and dataset columns before `train`. |
| Reload/predict fails after smoke training | Model was not saved due skip flags | Do not use `--skip_save_model` for workflows that need reload/prediction. |
| Resume starts from scratch | `model_resume_path` missing or invalid | Point to the run/model directory that still contains checkpoints/progress. |
| Out-of-memory | Batch/model too large or GPU allocation mismatch | Reduce batch size, use smaller model, verify `--gpus`, or use CPU/tiny smoke. |
| LLM quantization/generation complains about CUDA | Quantized LLM path needs GPU | Disable quantization for CPU tests or run on a verified CUDA machine. |
| Callback/tracking integration import fails | Missing contrib package | Install and configure only the requested tracker; avoid enabling all trackers. |
| Model card/training report warning appears | Post-training report writer failed | Treat as warning if training completed and artifacts exist; inspect logs if reports are required. |
