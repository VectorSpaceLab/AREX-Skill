# Runtime workflow and output checks

This reference describes the execution contract without defining dataset file
layouts. Obtain a valid scene input contract from `datasets-and-configuration`.

## 1. Prepare and preflight

1. Activate the environment built from the repository's `environment.yml`, or
   an equivalent environment with matching Torch/CUDA ABI and compiled
   extensions.
2. Export a compatible compiler before building extensions (`CC` and `CXX`).
   The repository README reports testing on RTX 3090/A6000 and the verified
   inspection report proves the pinned stack on an NVIDIA A100 SM80 host.
3. Check the active GPU and runtime:

   ```bash
   nvidia-smi
   python -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0), torch.version.cuda)'
   python -c 'import simple_knn._C, gaussian_rasterizer._C; print("extensions OK")'
   ```

4. Run `python run_slam.py --help` and the bundled `check_cli.py` against the
   scene config. These commands do not initialize SLAM.
5. Confirm an explicit, unique output directory and decide W&B state before a
   GPU run. `use_wandb: False` is the safe default.

There is no CPU execution mode. `GaussianModel` allocates CUDA tensors in its
constructor, `simple_knn._C.distCUDA2` is used for point spacing, and
`gaussian_rasterizer` renders on CUDA. CPU checks can validate YAML or isolated
math only; they cannot validate the SLAM pipeline.

## 2. Resolve the run contract

The command has one positional config and optional overrides:

```bash
DISABLE_WANDB=true python run_slam.py <config.yaml> \
  --input_path <scene-input> --output_path <unique-output> --seed 0
```

`load_config` recursively follows `inherit_from` and recursively updates the
base dictionary with the scene dictionary. Inheritance paths are opened as
written, so a relative inheritance path normally requires launching from the
repository root. Use a scene-specific config, not only a base dataset config,
because the base files do not contain the scene `data` block.

After loading and applying CLI overrides, `run_slam.py`:

1. forces `use_wandb` false only when `DISABLE_WANDB` is exactly `true`;
2. calls `wandb.init` and source-code logging if W&B remains enabled;
3. calls `setup_seed`;
4. constructs and runs `GaussianSLAM`;
5. constructs `Evaluator` from the output directory and saved `config.yaml`;
6. logs three evaluation JSON files to W&B if enabled; and
7. prints `All done.✨`.

The evaluator isolates its major phases with `try/except`; inspect files and
tracebacks rather than using the final print as the only success signal.

## 3. Main loop behavior

`GaussianSLAM.run()` creates an empty CUDA `GaussianModel`, initializes it,
and processes all dataset frames:

- frame 0 and frame 1 use the dataset-provided pose directly;
- later frames call `Tracker.track`, which initializes from configured ground
  truth, constant-speed extrapolation, or visual odometry and optimizes camera
  rotation/translation against rendered RGB/depth;
- mapping IDs are every `mapping.map_every` frame plus the last frame;
- at a boundary, the old model is saved to `submaps/<zero-padded-id>.ckpt`, the
  mapper keyframe state is cleared, and a fresh Gaussian model begins the new
  submap;
- mapping seeds points from the current RGB-D view, filters candidates based on
  the new/existing-submap mask, adds points through CUDA nearest-neighbor
  spacing, optimizes the submap, and writes a visual diagnostic;
- estimated poses are saved in `estimated_c2w.ckpt` after the loop.

Motion submaps compare the current estimated pose to the last submap-start pose
using source constants of 50 degrees and 0.5 translation. Fixed submaps use
`new_submap_every`; the source also includes the last frame in boundary IDs.
A boundary saves the prior submap before mapping the boundary frame. There is
no explicit post-loop save of the currently active Gaussian model. This is an
important output-completeness check for short fixtures and runs ending at a
boundary.

## 4. Validate outputs

At minimum, validate:

```text
<output>/config.yaml
<output>/estimated_c2w.ckpt
<output>/submaps/*.ckpt       (at least one for a non-empty normal run)
<output>/mapping_vis/*.jpg   (if mapping reached a visualisation step)
```

The constructor creates `mapping_vis/` and `tracking_vis/`; tracking currently
logs to the console/W&B rather than guaranteeing files in `tracking_vis/`.
Depending on evaluator success and dataset/config, additional artifacts may
include:

```text
rendering_metrics.json
reconstruction_metrics.json
ate_aligned.json
rendering_metrics.png
mesh/final_mesh.ply
<scene>_global_map.ply
nvs_eval/*.jpg
```

These are post-run evaluation products, not proof that the tracking/mapping
loop itself completed correctly. A missing evaluator file should be attributed
to the corresponding traceback, unsupported evaluation branch, or incomplete
submaps rather than silently fabricated.

The effective `config.yaml` is the strongest record of what ran. Preserve the
stdout/stderr log, host/GPU details, commit/version, and seed alongside it.
Use a fresh output path for any recovery attempt; the writer will otherwise
reuse existing directories and may mix old and new artifacts.

## 5. Reproducibility protocol

For each repeat:

- use the same effective YAML and explicit seed (paper averages use seeds 0,
  1, and 2 according to the README);
- keep the same GPU architecture and extension builds;
- set `DISABLE_WANDB=true` for a local reproducibility check unless logging is
  part of the experiment;
- give every seed a separate output path; and
- compare metrics with tolerance because differential rasterization is
  nondeterministic even though `setup_seed` fixes Python/NumPy/PyTorch/CUDA
  RNGs and disables cuDNN benchmark selection.

Do not use `--seed 0` as evidence of an override: the source applies it only in
an `if args.seed` truthiness branch, so zero is ignored. The config's `seed: 0`
is still effective when no CLI seed is supplied. Use a positive CLI seed or
edit YAML when testing CLI override behavior.
