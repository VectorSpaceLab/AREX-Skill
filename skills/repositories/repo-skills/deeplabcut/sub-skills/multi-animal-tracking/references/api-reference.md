# Multi-Animal Tracking API Reference

## Config concepts
- `multianimalproject`: enables multi-animal tracking code paths.
- `individuals`: ordered list of tracked identities. It drives the default `n_tracks` value.
- `identity`: set before training when individuals can be visually distinguished and should stay named consistently.
- `multianimalbodyparts`: body parts shared by every individual.
- `uniquebodyparts`: one-off landmarks or objects; outputs store them under `single` when present.
- `default_track_method`: saved tracker family when the caller does not override `track_method`.
- `skeleton`: optional connectivity used by skeleton-based assembly and plotting.
- `animal_names`: output naming override for stitched tracks. If provided, its length must match `n_tracks`.

## Track-method decision table

| Method | Use it when | Notes |
| --- | --- | --- |
| `ellipse` | baseline motion/shape tracking | common default; good first choice |
| `box` | box geometry is more stable or there is only one multianimal bodypart | the tracker is forced for one-bodypart projects |
| `skeleton` | the skeleton structure is the most reliable grouping cue | needs a meaningful skeleton graph |
| `ctd` | the model is conditional top-down | tracking happens during analysis; do not call manual convert/stitch |
| `transformer` | reID-assisted downstream output naming | produced by `transformer_reID` or `stitch_tracklets` with a transformer checkpoint; it is not the baseline convert tracker |

## `analyze_videos`

Signature summary: `analyze_videos(..., auto_track, n_tracks, animal_names, identity_only, ctd_tracking, ctd_conditions, ...)`

Important parameters:
- `auto_track=True` is the modern default; it already performs tracking and stitching for multi-animal projects.
- `auto_track=False` leaves raw detections in `_full.pickle` and `_assemblies.pickle`.
- `identity_only=True` tells the auto-tracking branch to rely on learned identities if available.
- `n_tracks` and `animal_names` control the reconstructed track count and output columns.
- `ctd_tracking` and `ctd_conditions` are for conditional top-down models; they bypass the manual tracking path.
- `snapshot_index` and `detector_snapshot_index` should match the analyzed model family.

Outputs to expect:
- `_full.pickle`
- `_meta.pickle`
- `_assemblies.pickle`
- optionally a prediction table when `save_as_df=True`
- for CTD tracking, a `_ctd`-named prediction table

## `convert_detections2tracklets`

Signature summary: `convert_detections2tracklets(..., track_method, identity_only, overwrite, destfolder, ...)`

Important parameters:
- `track_method`: `ellipse`, `box`, or `skeleton` for baseline conversion.
- `identity_only=True`: use identity scores rather than motion-based tracker assignment.
- `ignore_bodyparts`: drop body parts from the tracking cost.
- `overwrite`: replace an existing tracklet file when rerunning.
- `destfolder`: should point to the analysis outputs.

Behavior notes:
- `ctd` is rejected because CTD tracks during analysis.
- one multianimal bodypart forces `box` tracking.
- the output tracklet file stem depends on `track_method`: `_el.pickle`, `_bx.pickle`, or `_sk.pickle`.
- the call expects the `_full.pickle` and `_assemblies.pickle` produced by analysis.

## `stitch_tracklets`

Signature summary: `stitch_tracklets(..., n_tracks, animal_names, min_length, split_tracklets, prestitch_residuals, max_gap, track_method, transformer_checkpoint, save_as_csv, ...)`

Important parameters:
- `n_tracks`: reconstruct this many tracks; defaults to the config `individuals` count.
- `animal_names`: override output identity names; must match `n_tracks` if provided.
- `min_length`, `split_tracklets`, `prestitch_residuals`, `max_gap`: tracklet quality controls.
- `track_method`: chooses which tracklet file to load and how to interpret the output stem.
- `transformer_checkpoint`: add reID-assisted edge weights and stitch with the trained transformer.
- `save_as_csv`: write a CSV beside the stitched `.h5`.

Behavior notes:
- if `transformer_checkpoint` is used, the output stem gains a `tr` suffix.
- if `animal_names` is omitted, config `individuals` are used.
- if `n_tracks` and `animal_names` conflict, the call fails.
- `min_length` must be at least 3.

## `transformer_reID`

Signature summary: `transformer_reID(..., track_method, n_tracks, n_triplets, train_epochs, train_frac, destfolder, ...)`

Important parameters:
- `track_method`: baseline tracker family used to mine tracklets.
- `n_tracks`: expected number of animals in the video.
- `n_triplets`: number of mined triplets for training.
- `train_epochs`: reID training length.
- `train_frac`: train/test split for the triplet dataset.
- `destfolder`: where the triplets, features, and checkpoint are written.

Behavior notes:
- the wrapper creates the tracking dataset, trains the transformer, and then calls stitching with the generated checkpoint.
- the generated checkpoint name encodes `train_epochs`.
- if the feature dictionary is missing during stitching, the reID path was not prepared correctly.

## Output file map
- `_full.pickle`: raw detections
- `_meta.pickle`: metadata for the analyzed video
- `_assemblies.pickle`: multi-animal assemblies
- `_el.pickle`, `_bx.pickle`, `_sk.pickle`: baseline tracklets
- `_bpt_features.pickle`: transformer feature dictionary
- `_triplet_vector.npy`: mined triplets
- `dlc_transreid_<epochs>.pth`: transformer checkpoint
- `_el.h5`, `_bx.h5`, `_sk.h5`: stitched baseline tracks
- `_el_tr.h5`, `_bx_tr.h5`, `_sk_tr.h5`: transformer-assisted stitched tracks
