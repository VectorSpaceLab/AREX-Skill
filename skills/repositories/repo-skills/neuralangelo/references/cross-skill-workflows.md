# Neuralangelo Cross-Skill Workflows

Use this reference when a task spans data preparation, training, and mesh extraction. Open the owning sub-skill for detailed parameters after deciding the phase boundary.

## Workflow A: New Custom Capture to Mesh

1. **Capture classification**
   - Decide whether the scene is object-centric, outdoor/building-scale, or indoor/room-scale.
   - Confirm the user has image/video rights, enough parallax, stable exposure, and coverage of all target surfaces.
2. **Data preparation**
   - Route to `sub-skills/data-preparation/SKILL.md`.
   - Plan frame extraction and COLMAP or ingest an existing COLMAP model.
   - Validate `transforms.json` and generate a Neuralangelo YAML patch with the data-preparation helpers.
3. **Training smoke**
   - Route to `sub-skills/training-and-configs/SKILL.md`.
   - Plan a low-iteration run first, with reduced validation frequency and checkpoint interval.
   - Record the logdir, saved config, checkpoint cadence, and W&B/offline mode.
4. **Full training**
   - Remove smoke-only overrides once data loading and CUDA are proven.
   - Monitor validation renders and loss trends; fix data/bounds before increasing resolution or iteration count.
5. **Mesh extraction smoke**
   - Route to `sub-skills/mesh-extraction/SKILL.md`.
   - Extract a low-resolution non-textured mesh first.
   - Validate the PLY header and inspect scale/orientation/cropping/noise.
6. **Production mesh**
   - Increase resolution, adjust `block_res`, optionally add texturing, and decide whether `--keep_lcc` is safe.
   - Preserve the extraction command and validation result in the handoff.

## Workflow B: Existing Prepared Dataset to Training

Use when the user already has images and `transforms.json`.

1. Run `sub-skills/data-preparation/scripts/validate_transforms_json.py` on the metadata.
2. If no config exists, run `sub-skills/data-preparation/scripts/generate_config_from_images.py` to make a YAML patch.
3. Run `sub-skills/training-and-configs/scripts/inspect_config_summary.py` on the selected YAML.
4. Run `sub-skills/training-and-configs/scripts/plan_training_command.py` to generate a smoke launch.
5. Confirm CUDA/tiny-cuda-nn with `scripts/check_neuralangelo_environment.py --require-cuda`.
6. Execute the planned training command only after data/config/runtime checks are green.

## Workflow C: Existing Checkpoint to Mesh

Use when the user supplies a checkpoint and config/logdir.

1. Confirm the checkpoint belongs to the config and dataset root. Prefer the saved training `config.yaml` from the same log directory.
2. Validate the dataset `transforms.json` with the data-preparation validator; extraction uses the same bounds metadata.
3. Run `sub-skills/mesh-extraction/scripts/plan_mesh_extraction.py` to check paths and estimate normalized grid/block counts.
4. Use `scripts/run_neuralangelo_entrypoint.py --entrypoint extract-mesh -- --help` if the extraction CLI needs to be checked in the current environment.
5. Run a low-resolution extraction first, then validate the PLY with `sub-skills/mesh-extraction/scripts/validate_mesh_file.py`.
6. Tune resolution, `block_res`, texturing, and largest-component filtering based on the first mesh.

## Handoff Contracts

### Data Preparation to Training

Provide:

- Data root and image subdirectory.
- `transforms.json` validation status, image count, and unresolved warnings.
- `scene_type`, `sphere_center`, `sphere_radius`, `aabb_range`, and any manual readjust recommendations.
- Generated config path or config patch content.
- Whether exposure/white-balance embeddings are enabled.

### Training to Mesh Extraction

Provide:

- Saved training config path.
- Checkpoint path and whether it is final/best/latest/smoke.
- Iteration count and whether training completed or was interrupted.
- Dataset root and `transforms.json` status.
- GPU/memory notes from training.
- Any known quality issue: pose drift, cropped bounds, floaters, hollow surfaces, missing views, or exposure artifacts.

### Mesh Extraction to User

Provide:

- Extraction command or planner JSON.
- Resolution, block resolution, texturing, LCC setting, GPU count, and output path.
- PLY validation result and vertex/face counts.
- Visual inspection status if performed.
- Recommended next run if quality is not acceptable.

## Escalation Rules

- If pose/bounds are wrong, return to data preparation before retraining or extracting at higher resolution.
- If training OOMs, first reduce rays/samples/hash-grid or validation settings in training; do not jump to extraction tuning.
- If mesh extraction OOMs, first reduce `block_res`, then resolution; do not change training hyperparameters unless geometry quality itself is wrong.
- If imports fail, return to `references/installation-and-environment.md` and run the root checker.
- If the user asks to modify Neuralangelo source code, use this skill for API/config context, but treat code edits as a repository-maintenance task with normal tests and review.
