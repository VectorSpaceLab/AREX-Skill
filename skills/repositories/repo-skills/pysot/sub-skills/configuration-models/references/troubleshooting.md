# PySOT config/model troubleshooting

Use this reference after `scripts/validate_config.py` or a safe `ModelBuilder`/`build_tracker` smoke fails. Route video/snapshot execution, training datasets, and benchmark metrics to sibling sub-skills after the config itself is valid.

## Fast diagnosis table

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pysot'` | PySOT's `setup.py` installs distribution metadata for `toolkit`; the `pysot` package is normally imported from a checkout through PYTHONPATH or an editable-development setup. | Run from an environment where the PySOT checkout is importable, or add the checkout root to PYTHONPATH/editable install before running validation. |
| `ImportError: cannot import name region` or `toolkit.utils.region` build failure | Legacy evaluation extension not built; Cython 3 can break the extension build. | Build the extension in a compatible environment; use `Cython<3` for the legacy region extension. This mainly affects toolkit/evaluation, but it can surface during broad import checks. |
| YAML parse error | Indentation, tabs, unquoted strings, malformed lists, or invalid booleans. | Fix YAML syntax; keep booleans consistently `true`/`false` or `True`/`False`. |
| `Non-existent config key: ...` during `cfg.merge_from_file` | YAML contains a key that is not declared in PySOT's base YACS config. | Remove the unknown key, move it under an allowed `KWARGS` node if the factory actually consumes it, or extend the base config in code before using that YAML. |
| Validator reports missing `TRACK.TYPE` | The experiment YAML relies on defaults or is incomplete. | Add an explicit `TRACK` block with `TYPE`, `EXEMPLAR_SIZE`, `INSTANCE_SIZE`, `BASE_SIZE`, and `CONTEXT_AMOUNT`. |
| `Unsupported TRACK.TYPE` or `KeyError` in `build_tracker` | Tracker type not in PySOT's tracker map. | Use exactly `SiamRPNTracker`, `SiamMaskTracker`, or `SiamRPNLTTracker`. |
| `ANCHOR.ANCHOR_NUM` mismatch | Anchor ratios/scales changed without updating explicit anchor count. | Set `ANCHOR.ANCHOR_NUM = len(RATIOS) * len(SCALES)` and keep `RPN.KWARGS.anchor_num` aligned. |
| `RPN.KWARGS.anchor_num` mismatch | RPN output channels do not match anchor settings. | Update RPN kwargs to the same anchor count. |
| `size not match!` from `TrkDataset` | Training output-size formula is inconsistent. | Set `TRAIN.OUTPUT_SIZE = (TRAIN.SEARCH_SIZE - TRAIN.EXEMPLAR_SIZE) / ANCHOR.STRIDE + 1 + TRAIN.BASE_SIZE`. Route further data checks to training-data. |
| `SiamMaskTracker must have mask_head` or `refine_head` assertion | Config selects `SiamMaskTracker` but did not enable mask/refine model modules. | Set `MASK.MASK: true`, configure `MASK.TYPE: MaskCorr`, set `REFINE.REFINE: true`, and use `REFINE.TYPE: Refine`; or change tracker type to `SiamRPNTracker`. |
| PyTorch `size mismatch` or missing/unexpected keys when loading a snapshot | Snapshot was trained for a different backbone/RPN/mask/anchor/config. | Pair the snapshot with its original config or retrain/export a checkpoint for the edited model graph. |
| Reshape/channel errors in classification or bbox conversion | RPN anchor count, output channels, or feature-layer list inconsistent. | Check `ANCHOR.*`, `RPN.KWARGS.anchor_num`, `RPN.KWARGS.in_channels`, `ADJUST.KWARGS.out_channels`, and selected backbone layers. |
| Full test/train script fails on `.cuda()` or missing data/snapshot | Full native benchmark/training needs user-supplied snapshots/datasets and often CUDA. | Do not treat this as a config-validator failure; route to tracking-inference or training-data for asset/backend preflight. |

## Missing or incomplete config keys

The YACS defaults can fill many values, but normal PySOT experiment configs are explicit about model-defining sections. The bundled validator intentionally fails when the YAML file itself lacks `TRACK.TYPE` or other required paths, because relying on defaults can silently build a different tracker than the user intended.

Minimum inference YAML paths to inspect:

- `META_ARC`
- `BACKBONE.TYPE` and `BACKBONE.KWARGS`
- `ADJUST.ADJUST`; if true, `ADJUST.TYPE` and `ADJUST.KWARGS`
- `RPN.TYPE` and `RPN.KWARGS`
- `MASK.MASK`; if true, `MASK.TYPE`, `MASK.KWARGS`, `REFINE.REFINE`, and `REFINE.TYPE`
- `ANCHOR.STRIDE`, `ANCHOR.RATIOS`, `ANCHOR.SCALES`, `ANCHOR.ANCHOR_NUM`
- `TRACK.TYPE`, `TRACK.EXEMPLAR_SIZE`, `TRACK.INSTANCE_SIZE`, `TRACK.BASE_SIZE`, `TRACK.CONTEXT_AMOUNT`

If the user's config is intentionally a small override file, merge it with the full base experiment config outside this sub-skill first, then validate the merged YAML.

## Bad `TRACK.TYPE`

Allowed values are exact and case-sensitive:

- `SiamRPNTracker`
- `SiamMaskTracker`
- `SiamRPNLTTracker`

`build_tracker(model)` is a dictionary lookup, so strings such as `SiamRPN`, `siamrpn`, `SiamMask`, or `SiamRPNLongTerm` fail. Choose the tracker that matches the model modules:

- `SiamRPNTracker`: box-only RPN model.
- `SiamMaskTracker`: mask/refine model; requires mask and refine heads.
- `SiamRPNLTTracker`: long-term RPN model with lost-search and confidence thresholds.

## Anchor mismatch

Expected validator failure examples:

```text
ERROR: ANCHOR.ANCHOR_NUM=4 but len(RATIOS)*len(SCALES)=5
ERROR: RPN.KWARGS.anchor_num=4 but ANCHOR.ANCHOR_NUM=5
```

Fix both numbers together. If you changed `RATIOS` from five ratios to three ratios and kept one scale, set both values to `3`. If you keep five ratios and add a second scale, set both values to `10` and expect snapshot incompatibility unless the checkpoint was trained with that anchor layout.

## Snapshot/config mismatch

This sub-skill does not load snapshots, but config edits often cause later checkpoint-load failures. Diagnose from the changed model graph:

- Backbone mismatch: keys/channels around `backbone.*` differ.
- Neck mismatch: keys/channels around `neck.*` differ or `neck` is missing/unexpected.
- RPN mismatch: `rpn_head.*` channels differ, often from anchor count or multi-layer changes.
- Mask mismatch: `mask_head.*`/`refine_head.*` missing or unexpected.
- Tracker mismatch: SiamMask/SiamRPN/LT behavior expects different model outputs.

The safe answer is to restore the matching config for the snapshot. Editing hyperparameters such as `TRACK.PENALTY_K`, `TRACK.WINDOW_INFLUENCE`, or `TRACK.LR` is usually less dangerous than editing backbone/RPN/mask/anchor structure, but still affects reported metrics.

## Long-term config extra keys

The long-term ResNet config may include legacy convenience keys such as `BACKBONE.CHANNELS`, `ADJUST.ADJUST_CHANNEL`, or `RPN.WEIGHTED` outside declared YACS nodes. The base PySOT config rejects undeclared keys with `Non-existent config key: ...` during `cfg.merge_from_file`.

When validating or adapting such a config:

1. Keep the functional keys that are actually consumed by factories, especially `BACKBONE.KWARGS`, `ADJUST.KWARGS`, and `RPN.KWARGS`.
2. Remove or relocate undeclared convenience keys unless your local PySOT fork explicitly declares them.
3. Re-run the validator before any tracking run.

## Import and build issues relevant to config/model work

- If `pysot` imports fail but `toolkit` imports work, the environment likely installed only the `toolkit` distribution from package metadata. Use checkout/PYTHONPATH or editable-development import style for `pysot`.
- If broad environment checks fail on `toolkit.utils.region`, rebuild the extension with legacy-compatible Cython (`Cython<3`). Config/model validation itself does not need benchmark evaluation, but integrated checks may import toolkit modules.
- Historical full PySOT workflows were documented for older Python/PyTorch/CUDA stacks. A modern CPU-only PyTorch can be enough for config/model construction smoke, but it is not proof that full CUDA benchmark or training scripts will run.
- Mask tracking code uses older NumPy aliases in some paths; if runtime mask tracking later fails under NumPy 1.24+, use a compatible NumPy or patch the alias. This is a tracking runtime issue, but it often appears after choosing a SiamMask config.

## Expected synthetic validator failures

Use these for usability tests or quick sanity checks:

1. Remove `TRACK.TYPE` from an otherwise valid config. The validator should fail before construction with a missing required path.
2. Change `ANCHOR.ANCHOR_NUM` from `5` to `4` while leaving five ratios and one scale. The validator should fail with the computed anchor product and, if `RPN.KWARGS.anchor_num` still says `5`, explain the mismatch.
