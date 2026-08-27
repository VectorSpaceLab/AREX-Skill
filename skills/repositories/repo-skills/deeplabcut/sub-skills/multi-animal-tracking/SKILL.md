---
name: multi-animal-tracking
description: "Route maDLC tracking, tracklet conversion, stitching, and
  transformer reID for DeepLabCut."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Multi-Animal Tracking

Use this sub-skill for multi-animal pose outputs that must become stable identities and tracks.

## Use this sub-skill for
- choosing the tracking branch for a multi-animal project
- validating `multianimalproject`, `individuals`, `multianimalbodyparts`, `uniquebodyparts`, and `identity`
- converting analyzed detections into tracklets
- stitching tracklets into final tracks
- using transformer reID when animals cross or baseline tracking swaps identities
- checking whether the output files and track counts match the project configuration

## Route elsewhere when needed
- project creation, new project config layout, and data-path setup -> `install-and-project-setup`
- frame extraction, labeling, training-dataset creation, and data conversion -> `data-labeling-and-training-datasets`
- pose-network training, evaluation, and analysis -> `pytorch-training-evaluation-inference`
- filtering, labeled videos, trajectory plots, 3D utilities, and export tasks -> `postprocessing-3d-video-exports`

## Fast decision order
1. Confirm the project is multi-animal and that the names in the config are consistent.
2. If the model is conditional top-down, tracking happens during analysis and the manual convert/stitch steps are skipped.
3. If `auto_track=True`, `analyze_videos` already performs conversion and stitching.
4. If `auto_track=False`, use `convert_detections2tracklets` followed by `stitch_tracklets`.
5. If identity supervision was learned, try `identity_only=True` before adding more complex reID logic.
6. If identities still swap during crossings, use `transformer_reID` to mine triplets, train a transformer, and stitch with the resulting checkpoint.

## Key API anchors
- `analyze_videos(..., auto_track, n_tracks, animal_names, identity_only, ctd_tracking, ctd_conditions)`
- `convert_detections2tracklets(..., track_method, identity_only)`
- `stitch_tracklets(..., track_method, n_tracks, animal_names, transformer_checkpoint)`
- `transformer_reID(..., track_method, n_tracks, n_triplets, train_epochs)`

Baseline tracker families are `ellipse`, `box`, and `skeleton`; `ctd` is a direct-tracking branch during analysis, not a manual convert/stitch setting.

## Config facts to keep aligned
- `multianimalproject: true` enables the multi-animal tracking path.
- `individuals` sets the default output identity list and usually the default track count.
- `identity: true` should be set before training when animals can be told apart consistently.
- `multianimalbodyparts` are shared body parts for each individual.
- `uniquebodyparts` are seen once per frame and are stored as a `single` channel in the outputs.
- Keep individual names, body-part names, and `animal_names` stable so output columns stay consistent.
- If `animal_names` is used, keep its length aligned with `n_tracks`.

## Bundled runtime aids
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/plan_tracking_workflow.py`

## Output families to expect
- raw detections: `_full.pickle` and `_meta.pickle`
- multi-animal assemblies: `_assemblies.pickle`
- baseline tracklets: `_el.pickle`, `_bx.pickle`, or `_sk.pickle`
- reID training artifacts: `_bpt_features.pickle`, `_triplet_vector.npy`, and `dlc_transreid_<epochs>.pth`
- stitched tracks: `.h5` and optional `.csv`, with transformer-assisted runs carrying a `tr` suffix

## What not to do here
- do not route project setup or labeling into this sub-skill
- do not route network training or evaluation into this sub-skill
- do not route generic labeled-video or filtering tasks here
- do not call manual convert/stitch for CTD models
- do not use `identity_only` unless the model learned identity supervision

## Validation reminder
Use the bundled planner script to print a safe call order before running anything, then confirm the expected output files and track counts.
