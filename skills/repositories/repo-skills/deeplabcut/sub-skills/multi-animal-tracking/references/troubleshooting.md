# Multi-Animal Tracking Troubleshooting

## Fast checks
1. Confirm `multianimalproject`, `individuals`, `multianimalbodyparts`, `uniquebodyparts`, and `identity`.
2. Check which output files exist: `_full.pickle`, `_assemblies.pickle`, a tracklet pickle, and the final `.h5`.
3. Confirm the chosen `track_method` matches the branch: baseline (`ellipse` / `box` / `skeleton`) or CTD.
4. Confirm `n_tracks` and `animal_names` agree.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `This function is only required for multianimal projects!` | The project config is not marked as multi-animal. | Route project setup back to the setup sub-skill or enable `multianimalproject` in the project config before using tracking. |
| `CTD tracking occurs directly during video analysis` | Manual convert or stitch was called on a CTD model. | Use the CTD analysis branch instead of manual convert/stitch. |
| `Could not find the assembles file ...` | The analysis outputs are missing or the destination folder does not match the analysis run. | Rerun analysis on the same videos and destination folder before converting detections to tracklets. |
| `Tracklets already computed` | A previous tracklet file is already present. | Set `overwrite=True` or remove the stale tracklet file before rerunning. |
| `Invalid tracking method` | The tracker name is unsupported for this stage. | Use `ellipse`, `box`, or `skeleton` for baseline convert/stitch. Use `ctd` only through analysis. |
| Tracklets are empty or very short | Detections are too sparse, the tracker is misconfigured, or `pcutoff` is too strict. | Lower the cutoff only if it is truly suppressing good detections; otherwise tune the tracker parameters or improve the pose model. |
| Only one animal body part is tracked and the tracker switches to box | The project has one multianimal bodypart. | This is expected; keep `boundingboxslack` large enough for overlap checks. |
| `n_tracks` and `animal_names` conflict | The explicit track count does not match the name list length. | Make the list length equal `n_tracks` or omit one of the arguments. |
| `identity_only=True` does not help | Identity supervision was not trained or the labels are inconsistent. | Set `identity: true` before training and relabel inconsistent identities with stable names. |
| Animals swap identities when they cross | Baseline motion tracking is not enough for the scene. | Try `identity_only=True` first; if that still fails, use `transformer_reID` with more triplets and epochs. |
| `checkpoint ... not found` | The reID training did not produce the expected checkpoint name. | Match the checkpoint to the `train_epochs` value or rerun the reID training step. |
| `did you run transformer_reID()?` or missing feature dict | The stitch call expected the reID feature dictionary but it was never created. | Run the reID wrapper first, or stitch only baseline tracklets without a transformer checkpoint. |
| Final output exists but the track names look generic | `animal_names` was omitted or too short. | Pass a full `animal_names` list or accept the config `individuals` ordering. |
| Manual convert/stitch succeeds but the output still looks noisy | The tracker family is right but the tuneable thresholds are not. | Adjust `boundingboxslack`, `iou_threshold`, `max_age`, and `min_hits`, then rerun conversion and stitching. |

## Tracker tuning hints
- `boundingboxslack`: grows the box used for linking; raise it when box overlap is too fragile.
- `iou_threshold`: tighter or looser box linking gate.
- `max_age`: how long a lost tracklet can survive before being considered new.
- `min_hits`: how many consecutive detections are needed before a track is trusted.
- `split_tracklets=False` can help when you trust long reID stretches and do not want gaps split aggressively.
- `prestitch_residuals=True` groups residuals by temporal proximity before the graph solve.

## Validation reminders
- If only `_full.pickle` exists, you are still at the analysis stage.
- If only a tracklet pickle exists, stitching has not been run yet.
- If the final `.h5` exists but the identities are wrong, the problem is usually identity consistency, `n_tracks`, or the tracker family, not the file writer.
- For visual output validation, hand off to the postprocessing sub-skill rather than inventing a new tracking step.
