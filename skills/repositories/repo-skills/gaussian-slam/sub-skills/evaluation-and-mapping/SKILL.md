---
name: evaluation-and-mapping
description: "Run and interpret Gaussian-SLAM trajectory, rendering, Replica
  mesh, global-map, and ScanNet++ novel-view evaluation from a completed
  checkpoint; verify artifact contracts, preserve partial-stage evidence, and
  recover common CUDA/Open3D/data failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation and mapping

Use this sub-skill when a Gaussian-SLAM run already has a checkpoint and the
Researcher needs metrics, a Replica reconstruction, or a refined global map.
It covers `run_evaluation.py` and the `Evaluator` lifecycle. It does **not**
train or resume SLAM, download datasets, repair checkpoints, or claim that a
partial metric set is a complete evaluation.

Read the focused reference before acting:

- [api-reference.md](references/api-reference.md): public entry points,
  checkpoint schema, stage behavior, and implementation defaults.
- [workflows.md](references/workflows.md): preflight, command, stage, and
  recovery procedures.
- [outputs-and-metrics.md](references/outputs-and-metrics.md): artifact and
  metric interpretation, including dataset gates and units.
- [troubleshooting.md](references/troubleshooting.md): failure diagnosis and
  safe recovery.

## Operating contract

### Inputs

Require all of the following before an expensive run:

1. A completed or intentionally partial checkpoint directory.
2. `config.yaml` in that directory, or an explicit compatible config path.
3. `estimated_c2w.ckpt` and a `submaps/` directory containing numbered
   submap checkpoints. Each submap should contain `gaussian_params` and
   `submap_keyframes` as produced by Gaussian-SLAM.
4. The dataset named by the config and its ground-truth assets at the paths
   resolved by that config.
5. A CUDA-capable runtime for the `Evaluator`: rendering, Replica mesh
   reconstruction, and global-map merging/refinement all use CUDA-bound model
   and rasterizer/FAISS code. A CPU-only trajectory helper check is useful
   support validation, but is not a substitute for a full evaluation.

Treat checkpoint files as untrusted inputs. Do not overwrite, prune, rewrite,
move, or repair them unless the user explicitly requests a separate operation.
The repository evaluator writes results *inside* the checkpoint directory;
make a copy or select a disposable output tree when preserving the source run
matters.

### Safe preflight

Run the bundled scripts before importing the repository evaluator:

```bash
python skills/disco/gaussian-slam/sub-skills/evaluation-and-mapping/scripts/check_cli.py \
  --checkpoint /path/to/checkpoint
python skills/disco/gaussian-slam/sub-skills/evaluation-and-mapping/scripts/validate_checkpoint.py \
  --checkpoint /path/to/checkpoint
```

These scripts are read-only, do not import PyTorch/Open3D, do not access the
network, do not open GUI windows, and do not write a report. They check paths,
configuration text, and the file-level schema only; they cannot prove that a
serialized tensor can be loaded on CUDA. Use `--json` for machine-readable
output. Fix missing required artifacts before starting `run_evaluation.py`.

### Standard invocation

From the repository root, with the project environment active:

```bash
python run_evaluation.py \
  --checkpoint_path /path/to/checkpoint \
  --config_path /path/to/checkpoint/config.yaml
```

If `--config_path` is omitted, the wrapper uses
`<checkpoint_path>/config.yaml`. The evaluator has no dry-run flag and no
separate output directory option. `save_render` is false in this wrapper, but
JSON, plots, meshes, and NVS images are still written under the checkpoint.
Do not run the command merely to test `--help` or schema validity.

### Lifecycle and stage interpretation

`Evaluator.__init__` loads the merged config, seeds the run, constructs the
configured dataset, fixes `device="cuda"`, reads `estimated_c2w.ckpt`, and
discovers submaps. It then runs these independent stages:

1. **Trajectory** — compares estimated and ground-truth camera translations,
   writes raw and Horn-aligned ATE, and plots trajectories.
2. **Rendering** — loads every `*.ckpt` submap and renders its keyframes for
   PSNR, LPIPS, SSIM, and train-view depth L1.
3. **Reconstruction** — only for `dataset_name: replica`; integrates rendered
   RGB-D frames into a mesh and evaluates it against Replica assets.
4. **Global map** — merges and deduplicates submap points, refines a Gaussian
   map for 10,000 iterations, saves a PLY, and, only for
   `dataset_name: scannetpp`, renders test-split NVS images and reports NVS
   PSNR to stdout.

Each call in `Evaluator.run()` is wrapped in its own broad exception handler.
A later stage can therefore succeed after an earlier stage fails. Always
inspect the output files and logs stage by stage; a process that reaches the
end is not proof that all four stages completed. Conversely, constructor
failures happen before those per-stage catches and prevent the run entirely.

### Required distinctions

- Reconstruction is explicitly skipped for every non-Replica dataset.
- Global-map creation is attempted for all datasets, but NVS evaluation is
  explicitly supported only for ScanNet++ (`dataset_name: scannetpp`).
- `depth_L1` in the reconstruction result is not the same as rendering
  `depth_l1_train_view`. The former needs Replica ground-truth mesh and unseen
  points plus headless Open3D; the latter is a rendered training-view average.
- Headless Open3D and the `evaluate_3d_reconstruction` package are required for
  the full Replica reconstruction path. A CPU trajectory result alone cannot
  validate those dependencies.
- CUDA is required for rendering/global-map paths. Do not silently downgrade
  them to CPU and report success.

## Procedure

1. Identify the dataset, scene, checkpoint provenance, and whether preserving
   the source checkpoint is required.
2. Run both read-only preflight scripts and record warnings.
3. Check that the configured input dataset and, for Replica reconstruction,
   `data/Replica-SLAM/cull_replica/<scene>.ply` plus
   `<scene>_pc_unseen.npy` are present. Do not download missing assets in this
   sub-skill.
4. Confirm CUDA, the differential Gaussian rasterizer, FAISS GPU, Open3D, and
   `evaluate_3d_reconstruction` in the intended environment. Use the
   environment contract in [workflows.md](references/workflows.md).
5. Run the standard command once. Do not concurrently evaluate the same
   checkpoint because stages write shared files.
6. Record which stage files exist, which stages printed exceptions, and which
   metrics are absent or `null`. Preserve traceback text for recovery.
7. Interpret values using [outputs-and-metrics.md](references/outputs-and-metrics.md),
   retaining dataset gates and implementation caveats.
8. If a stage fails, apply the smallest non-mutating recovery in
   [troubleshooting.md](references/troubleshooting.md). Re-run against a copy
   if the original output must remain reproducible.
9. Report complete, partial, skipped, and unverified stages separately.

## Safe scripting rules

Bundled scripts must remain read-only by default. They must not run the
expensive evaluator, import heavy CUDA/Open3D modules, open Open3D windows,
download weights or datasets, or mutate user checkpoints. Keep review logs and
verification cases outside this runtime skill directory.
