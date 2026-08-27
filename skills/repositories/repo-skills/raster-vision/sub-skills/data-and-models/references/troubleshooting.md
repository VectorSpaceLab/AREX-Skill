# Troubleshooting

Use this reference when a Raster Vision config parses but the scene, dataset, or bundle still fails at build / load / predict time.

## Fast first checks

1. Run `scripts/check_scene_config.py` against the raw `SceneConfig` JSON.
2. Confirm the `ClassConfig` matches the task and that colors / null class are valid.
3. Check raster / label bbox alignment and AOI CRS.
4. Check `channel_order` and raster transformers before blaming the model.
5. Check that GeoJSON features carry the expected geometry type and `class_id` fields.

## Common failure patterns

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValidationError` about class names / colors | `ClassConfig` length mismatch or invalid `null_class`. | Make `names` and `colors` the same length, or omit `colors`; keep `null_class` inside `names`. |
| `All training scene ids must be unique` | Duplicate ids across train scenes. | Rename the duplicate scene ids. |
| `IDs ... do not match any scene in the dataset` | `scene_groups` references stale ids. | Update the group membership or rebuild the scene ids. |
| `SceneConfig` build complains about missing class config | The scene uses a label source or label store. | Supply `--class-config-json` in the checker or pass a real `ClassConfig` when building. |
| AOIs seem clipped or shifted | AOI CRS or scene bbox mismatch. | Supply polygon / multipolygon AOIs in EPSG:4326 and verify the imagery CRS. |
| `ChannelOrderError` | `channel_order` points past the raw channel count. | Remove the invalid index or use a valid subset / reorder. |
| Raster / label arrays look off by one band | The source has an alpha band or the wrong transformer stack. | Let Raster Vision pick bands automatically, or set an explicit `channel_order`. |
| Albumentations complains about dtype | Imagery is not in the expected range / dtype. | Add `MinMaxTransformer`, `StatsTransformer`, or `CastTransformer` before the dataset sees the chips. |
| `LineStrings and Points are not supported` | The label source expects polygons. | Add buffering via a `BufferTransformer` or use polygon labels. |
| `background_class_id is required if infer_cells=True` | Chip classification is inferring cells without a background class. | Set `background_class_id` and, if needed, `cell_sz`. |
| `cell_sz is not set` | A chip-classification grid is being inferred without explicit size. | Set `cell_sz` or let the surrounding pipeline fill it from chip options. |
| `group_train_sz specified without group_uris` | `ImageDataConfig` group sizing fields were mixed incorrectly. | Specify `group_uris` first, then one of `group_train_sz` or `group_train_sz_rel`. |
| `Specify either size_lims or h and w lims` | Invalid `WindowSamplingConfig` random-window settings. | Use `size_lims` or both `h_lims` and `w_lims`, not both styles. |
| `run_tensorboard if log_tensorboard is False` | Conflicting learner config flags. | Turn on `log_tensorboard` or disable `run_tensorboard`. |
| `class_loss_weights ... must be same length as the number of classes` | Solver weights do not match the class list. | Realign the weight vector with the `ClassConfig`. |
| `FileExistsError` for `scores.tif` | A semantic-segmentation store found incompatible existing outputs. | Clear the output dir or match the class count / dtype / smooth-output mode. |
| `neg_ratio specified, but no bboxes found` | Negative sampling was requested without positives in scene or AOI. | Verify the training labels and AOI coverage. |
| `raster_source in model bundle must have uris` / `label_store in model bundle must have uri` | The bundle is not a valid prediction bundle for `Predictor`. | Rebuild the bundle from a proper Raster Vision pipeline. |
| Predict output looks shifted or wrong-band | The bundle's original `channel_order` no longer matches the target imagery. | Override with the core `Predictor` / CLI `--channel-order` path or rebuild with the correct band order. |

## When to stop

If the config is valid but the scene still cannot build, the failure is usually one of:
- missing source files or unreadable URIs
- incompatible CRS / bbox / AOI assumptions
- a label store that already exists with incompatible contents
- an insufficient `ClassConfig` for the requested label source or prediction mode
