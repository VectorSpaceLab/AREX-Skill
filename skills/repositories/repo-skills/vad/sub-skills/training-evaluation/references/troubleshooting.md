# Training/evaluation troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Help or command fails on `*_ext`/`ball_query_ext` before argparse | Legacy MMDetection3D native extensions are unavailable | Repair the exact CUDA/PyTorch/MMDetection3D build; do not infer a usable runtime from a parsed config. |
| Dataset/annotation `FileNotFoundError` | Relative `data_root`, temporal PKL, map annotation, or CAN-bus input is missing | Run [data-preparation](../../data-preparation/SKILL.md)'s layout checker and make train/val/test paths consistent. |
| `VAD`/custom dataset not found in registry | Plugin was not imported or `plugin_dir` is resolved from the wrong working directory | Check config plugin fields and run the config contract checker; launch from a context where the plugin package is importable. |
| Stage 2 cannot load checkpoint | `load_from` points to a missing or mismatched stage-1 file | Train/select the matching stage-1 model and update the path; tiny and base checkpoints are not interchangeable. |
| Evaluation metrics change unexpectedly or visualization is wrong | Released checkpoint uses the legacy normalization but config uses the newer setting | Apply `mean=[103.530,116.280,123.675]`, `std=[1,1,1]`, `to_rgb=False` for released weights and keep the choice recorded. |
| Distributed evaluation gives suspicious metrics | Project-specific warning: multi-GPU evaluation can be inaccurate | Re-run with one GPU and `--launcher none`; do not use `--gpu-collect` as a correctness fix. |
| `--options`/`--cfg-options` or `--eval-options` conflict | Both deprecated and replacement flag were supplied | Use only `--cfg-options` for config and only `--eval-options` for evaluation kwargs. Quote nested lists/tuples. |
| CUDA OOM or workers hang | Image/queue/model workload exceeds GPU or worker resources | Start with the smallest intended config/GPU, reduce workers only through a deliberate config override, and preserve the experiment record. Do not claim a CPU fallback for the model. |
| No artifact for visualization | `--out` was omitted and no `show`/`show-dir` was used | Re-run evaluation with `--out RESULTS.pkl` or use the dataset formatting route, then inspect the artifact before rendering. |
