# UniAD cross-cutting troubleshooting

## First triage route

1. Import/version/plugin error before config builds: read `references/installation.md` and run `scripts/check_uniad_environment.py`.
2. Dataset or annotation path error: route to `sub-skills/data-preparation/`.
3. Wrong config, missing head, BEV encoder swap, queue-length tradeoff, or planning metric question: route to `sub-skills/config-and-model-architecture/`.
4. Distributed launch, checkpoint, GPU memory, or metric reproduction issue: route to `sub-skills/training-evaluation/`.
5. Result pickle, rendering, or video issue: route to `sub-skills/visualization-and-results/`.

## Common symptoms

| Symptom | Likely cause | Route/recovery |
|---|---|---|
| `ModuleNotFoundError: projects.mmdet3d_plugin` | Command not launched from the UniAD root or `PYTHONPATH` missing the repo root. | Set `PYTHONPATH="$(pwd)":$PYTHONPATH` from the checkout root; rerun plugin import check. |
| `AssertionError: MMCV==... is used but incompatible` | OpenMMLab package versions are inconsistent. | Reinstall the documented stack or a tested compatible stack; avoid mixing MMCV 2.x with MMDetection 2.x configs. |
| `ImportError` from `mmcv.ops` or deformable attention | `mmcv-full` wheel does not match Torch/CUDA or compiled ops are missing. | Install `mmcv-full` for the exact Torch/CUDA wheel; verify CUDA availability and a tiny tensor allocation. |
| NumPy `_ARRAY_API`/`multiarray failed to import` | NumPy 2.x with extensions built for NumPy 1.x. | Use UniAD's NumPy 1.x pin. |
| Annotation PKL missing | `data/infos/` not prepared. | Use `data-preparation` layout checks and command builder. |
| Stage-2 run fails around motion/planning anchors | `data/others/motion_anchor_infos_mode6.pkl` missing or config points elsewhere. | Validate motion-anchor file and config paths. |
| Evaluation refuses non-distributed mode | Source `tools/test.py` disables the non-distributed branch. | Use the distributed launcher shape from `training-evaluation`, even for one GPU. |
| Visualization cannot find task keys | The result pickle came from a config without that task head or from an incomplete run. | Inspect the pickle with `visualization-and-results/scripts/inspect_results_pickle.py` and confirm config/head ownership. |

## Safe preflight sequence

```bash
python <path-to-this-skill>/scripts/check_uniad_environment.py --repo-root . --configs
```

Run that command from a UniAD checkout, or pass `--repo-root` to the checkout that should be inspected. Then validate data layout and render train/eval commands from the sub-skills instead of launching an expensive job immediately.
