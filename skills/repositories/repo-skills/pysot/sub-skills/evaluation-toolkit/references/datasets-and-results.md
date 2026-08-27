# Datasets And Tracker Result Layouts

This reference describes the dataset adapter names and result-tree shapes consumed by PySOT’s evaluation toolkit. It is self-contained operating guidance; use user-provided benchmark files and tracker outputs rather than relying on any generated or local production artifacts.

## Evaluation root convention

The evaluation CLI takes `--tracker_path` and `--dataset` and then looks for trackers with:

```text
<tracker_path>/<dataset>/<tracker_prefix*>
```

For each matched tracker directory, the dataset adapter loads per-video result files from family-specific locations under that tracker directory.

The default tracking workflow writes results under:

```text
results/<dataset>/<snapshot_base_name>/...
```

So the usual evaluation argument is `--tracker_path results --dataset <dataset> --tracker_prefix <snapshot-or-tracker-prefix>`.

## Dataset sidecars

Full metric evaluation requires benchmark content under:

```text
testing_dataset/<dataset>/<dataset>.json
```

The JSON sidecar drives the toolkit adapters. Common fields are:

- `video_dir`: directory for a sequence.
- `init_rect`: initial bounding box.
- `img_names`: frame image paths used by the `Video` loader.
- `gt_rect`: ground-truth trajectory.
- `attr`: attributes for OPE datasets when available.
- LaSOT also uses `absent` to mask absent frames.
- VOT short-term sidecars include tag arrays such as `camera_motion`, `illum_change`, `motion_change`, `size_change`, and `occlusion`.

The bundled validator in `../scripts/validate_results_layout.py` intentionally does not require this dataset tree. It only checks tracker result layout before a full evaluation attempt.

## Supported families and CLI routing

| Dataset name pattern | Adapter class | Metric branch in evaluation CLI | Notes |
| --- | --- | --- | --- |
| Names containing `OTB`, for example `OTB100`, `OTB2015`, `OTB50` | `OTBDataset` | OPE success + precision | `CVPR13` JSON sidecar may exist in OTB data, but the stock CLI branch is selected by the string `OTB`; use an OTB-containing dataset name unless adapting code. |
| Exactly `LaSOT` | `LaSOTDataset` | OPE success + precision + norm precision | `absent` mask is applied before OPE metric curves. |
| Names containing `UAV`, for example `UAV123`, `UAV20L` | `UAVDataset` | OPE success + precision | Same direct per-video result-file layout as OTB. |
| Names containing `NFS`, for example `NFS30`, `NFS240` | `NFSDataset` | OPE success + precision | Same direct per-video result-file layout as OTB. |
| `VOT2016`, `VOT2017`, `VOT2018`, `VOT2019` | `VOTDataset` | Accuracy/Robustness + EAO | Short-term restart protocol with `baseline/<video>/<video>_001.txt` files. |
| Exactly `VOT2018-LT` | `VOTLTDataset` | F1 | Long-term protocol with trajectory and confidence files. |
| `GOT-10k` | `GOT10kDataset` | Not evaluated by the stock evaluation CLI | The tracking workflow writes server-style result files; use GOT-10k server tooling or adapted evaluation. |
| `TrackingNet` | `TrackingNetDataset` | Not evaluated by the stock evaluation CLI | Server benchmark; result layout may need benchmark-specific packaging outside PySOT’s Python evaluator. |

## OPE-family result files

Used by OTB, LaSOT, UAV, and NFS branches:

```text
<tracker_path>/<dataset>/<tracker_name>/<video>.txt
```

Each line is normally a comma-separated rectangle:

```text
x,y,width,height
```

Operational notes:

- There should be one line per benchmark frame.
- `OTBVideo` has fallback names for several legacy sequences if `<video>.txt` is not present: `fleetface.txt`, `jogging_1.txt`, `jogging_2.txt`, `skating2_1.txt`, `skating2_2.txt`, `faceocc1.txt`, `faceocc2.txt`, `human4_2.txt`, or lowercased first letter plus `.txt`.
- LaSOT truncates `monkey-17` predictions to the ground-truth length in its adapter.
- OPE evaluation can print shape/length mismatches, but it may continue; treat mismatched frame counts as a result-generation issue and route to `../tracking-inference/` if files were produced by a tracker run.

## VOT short-term result files

Used by `VOT2016`, `VOT2017`, `VOT2018`, and `VOT2019` evaluation:

```text
<tracker_path>/<dataset>/<tracker_name>/baseline/<video>/<video>_001.txt
```

The VOT adapter searches for `*0*.txt` under each `baseline/<video>/` directory. If 15 restart repetitions are present, it uses all 15; otherwise it uses the first matched file.

Rows can be:

- `1`: initialization frame.
- `2`: tracking failure/lost target.
- `0`: skipped frame after failure.
- `x,y,width,height`: rectangle prediction.
- `x1,y1,x2,y2,x3,y3,x4,y4`: polygon prediction, often from mask-enabled trackers.

VOT metrics use the compiled `toolkit.utils.region` extension for overlap calculations.

## VOT2018-LT result files

Used by `VOT2018-LT` F1 evaluation:

```text
<tracker_path>/<dataset>/<tracker_name>/longterm/<video>/<video>_001.txt
<tracker_path>/<dataset>/<tracker_name>/longterm/<video>/<video>_001_confidence.value
<tracker_path>/<dataset>/<tracker_name>/longterm/<video>/<video>_time.txt
```

The F1 evaluator consumes trajectory and confidence files. The time file is produced by the tracking workflow but is not used by the F1 benchmark class.

Trajectory rows are comma-separated boxes or `[0]`/single-value unknown markers. Confidence values are read from the second line onward, with an inserted NaN for the first frame; the first confidence line is commonly blank.

## GOT-10k server-style result files

The tracking workflow writes GOT-10k-style outputs under:

```text
<tracker_path>/<dataset>/<tracker_name>/<video>/<video>_001.txt
<tracker_path>/<dataset>/<tracker_name>/<video>/<video>_time.txt
```

Each trajectory row is a comma-separated rectangle. PySOT’s stock evaluation CLI does not compute GOT-10k scores. Validate shape locally, then package according to the benchmark server requirements outside this Python evaluator.

## Hyperparameter-search result root

The hyperparameter-search workflow writes many tracker directories using parameterized names. For non-server datasets the root is typically:

```text
hp_search_result/<dataset>/<snapshot_base>_r<search_region>_pk-<penalty>_wi-<window>_lr-<lr>/...
```

The inner layout follows the same family rules above: VOT short-term uses `baseline/`, VOT2018-LT uses `longterm/`, and OPE datasets use direct `<video>.txt` files.

For GOT-10k, the source workflow nests results under an additional `epoch_result/` prefix before the hp-search path; treat these as server-style outputs, not stock Python-eval inputs.
