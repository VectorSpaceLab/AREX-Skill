# Segmentation troubleshooting

Preserve the exact command, config, Python/Paddle versions, device, source
revision, and whether the failure occurred during parsing, import, model build,
forward, data loading, checkpoint load, or metric accumulation. Diagnose first;
do not change model, labels, and environment simultaneously.

## Failure map

| Symptom | Likely cause and action |
|---|---|
| Dataset is unsupported | `DATA.DATASET` is not an exact registered key. Use the factory spelling or add/test a dataset class. |
| Root/file-list errors | Wrong `DATA.DATA_PATH`, split, suffix, or missing conversion artifact. Run the read-only layout validator. |
| Counts look right but pairs are wrong | ADE20K `.jpg`→`.png`, Cityscapes sorted zip, or Trans10k sorted zip mismatch. Compare logical stems and sample dimensions. |
| ADE20K metrics are nonsensical | Raw class-0 offset was not subtracted or ignored pixels were not restored to 255. Inspect unique ids. |
| TopFormer returns no model/attribute error | Current factory checks `TopFomer`, not `TopFormer`. Preserve the typo or apply/test a deliberate source fix. |
| UperNet has no `aux_decoder` | Current `forward` calls it even when `AUXIHEAD` is false. Start from a known auxiliary-enabled config or patch/test. |
| Unknown YAML key or shape error | Incomplete family config or conflicting inherited `BASE`. Start from a complete family YAML and compare all dimensions. |
| Checkpoint has many missing/shape warnings | Full segmentation weights, backbone weights, class count, decoder, and architecture were confused or differ. Inspect load counts and stop if compatibility is unresolved. |
| Positional embedding mismatch | Patch grid differs. The loader may interpolate some ViT embeddings, but it cannot repair arbitrary heads; run an approved forward before trusting it. |
| Resume cannot find `.pdopt` | `--resume` derives the sibling by replacing `.pdparams` and `model` with `opt`; supply the exact matching pair. |
| Resume starts at an unexpected iteration | Optimizer/scheduler state is stale or from another run. Verify `LR_Scheduler.last_epoch` and the pair. |
| Validation fallback missing | `--model_path` was omitted and `SAVE_DIR/iter_{TRAIN.ITERS}_model_state.pdparams` is absent. Pass the full file explicitly. |
| `--multi_scales False` still enables it | `argparse type=bool` treats nonempty `False` as true. Omit the flag for single-scale. |
| Demo deletes source results/images | Existing `results_dir` is recursively removed. Use a new output and ensure it is not the input or its ancestor. |
| Demo crashes on a JSON/directory | It loops through all `os.listdir(img_dir)` entries. Keep `img_dir` image-only. |
| Demo fails around `pretrained_backbone` | `config.update_config` tests membership on `argparse.Namespace` in this checkout. Record the error and make an approved attribute-access patch before retrying. |
| Overlay exists but no metric | Demo is inference-only. Use `val.py` with labels for mIoU, accuracy, and Kappa. |
| Masks are shifted/noisy | Label resize used bilinear interpolation. Enforce nearest-neighbor and paired geometry. |
| Foreground ignored or loss crashes | Actual mask ids disagree with `TRAIN.IGNORE_INDEX`, class count, or ADE offset. Inspect sampled ids and align the contract. |
| A few validation samples disappear | The validation distributed sampler uses `drop_last=True`; record the remainder or make a controlled evaluation change. |
| CPU import fails | Paddle/source optional dependency is unavailable. Stop at static evidence or select a prepared environment; do not claim model verification. |
| CUDA build/forward fails | Paddle/CUDA/operator incompatibility or OOM. Probe device, try a tiny approved config, reduce batch/crop, and classify backend versus memory. |
| Multi-scale/slide OOM or stalls | Crop, scale list, model, or batch is too large. Start with one-scale/non-slide/tiny approved smoke; multi-scale is separately budgeted. |
| Converter import fails | `mmcv`, `detail`, or Cityscapes tools are optional and not all are in `requirements.txt`. Prepare dependencies explicitly; never install/download implicitly. |
| Converter mutates unexpected files | Tools default toward dataset-tree writes. Use a copied/staged root and inspect generated paths. |

## CPU parser versus GPU forward

Use precise evidence labels:

- **Static/parser:** help, YAML/BASE readability, option names, paths, pairs,
  checkpoint existence, and bounded label metadata. No Paddle model is built.
- **CPU construction:** Paddle imports, registry resolves, and the selected
  model allocates/builds on CPU. This may still be memory-heavy.
- **GPU smoke:** selected config/model performs a bounded tiny forward or one
  batch on the target Paddle/CUDA environment.
- **Task validation:** real data and compatible full weights produce metrics.

Paddle GPU 2.6.2 and a passing CUDA smoke are useful environment facts, not
proof that every historical 2021-era segmentation model is compatible. The
README's historical Paddle 2.1/CUDA 10.2 claim is a version-drift risk.

## Recovery order

1. Run `--help` on both source-independent scripts and preserve stdout/errors.
2. Validate the exact dataset split, stems, dimensions, label ids, class count,
   and ignore id without importing the source.
3. Inspect the complete family YAML and recursive `BASE` values; verify model
   name/decoder/backbone/head dimensions and normalization.
4. Check full model and backbone checkpoint paths separately. Never substitute a
   backbone state dict for `--model_path`.
5. Reproduce with one GPU, one scale, one batch, and a known family config
   before distributed, slide, multi-scale, or training work.
6. After changing class count, crop geometry, decoder, normalization, or weight
   source, repeat layout/compatibility and synthetic checks.
7. Report missing data/weights, skipped conversion, dropped samples, absent
   backend support, and all intentionally skipped expensive work.

The requested English `docs/paddlevit-predict.md` is not present in this
checkout. The available `docs/paddlevit-predict-cn.md` is a classification
prediction tutorial, not evidence for this segmentation demo; treat the
segmentation README and `demo/demo.py` as the authoritative demo contract.
