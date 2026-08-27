# Outputs and metrics

## Artifact contract

The evaluator uses the checkpoint directory as both input and output. Treat
these as stage-scoped artifacts:

```text
<checkpoint>/
  config.yaml                 # input, written by SLAM
  estimated_c2w.ckpt          # input pose tensor
  submaps/*.ckpt              # input Gaussian submaps
  ate.json                    # trajectory output
  ate_aligned.json            # trajectory output
  eval_trajectory.png         # trajectory plot
  rendering_metrics.json      # rendering output
  rendering_metrics.png       # rendering plot
  rendered_imgs/*.png         # only when save_render=True in custom code
  mesh/final_mesh.ply         # Replica reconstruction output
  mesh/cleaned_mesh.ply       # cleaned Replica mesh output
  reconstruction_metrics.json # Replica reconstruction output
  <scene>_global_map.ply      # global-map output
  nvs_eval/*.jpg              # ScanNet++ only
```

The final three groups are conditional. Existing files from an earlier run
can remain after a later partial run, so check modification times or evaluate
in a fresh copy. The evaluator does not write a stage manifest or a complete
summary JSON.

## Trajectory metrics

`ate.json` and `ate_aligned.json` each contain:

```json
{
  "compared_pose_pairs": 123,
  "rmse": 0.012,
  "mean": 0.010,
  "median": 0.009,
  "std": 0.006,
  "min": 0.001,
  "max": 0.031
}
```

The values are Euclidean translation errors in the dataset's coordinate unit
(Replica-style meter data is commonly described in meters; the plot and
console print RMSE in centimeters by multiplying by 100). `ate.json` compares
estimated translations directly to GT. `ate_aligned.json` first applies a
Horn closed-form rigid alignment to the translation point clouds; it is not a
scale-aligned Sim(3) metric and does not align rotations for the reported
error.

Ground truth is truncated only when GT is longer than the estimate. Entries
with non-finite GT pose elements are removed from both arrays. A GT trajectory
shorter than the estimate, unequal lengths after filtering, an empty valid
set, or malformed pose dimensions can fail the stage; do not infer a valid
ATE from a plot alone.

## Rendering metrics

`rendering_metrics.json` contains the arithmetic mean over every submap
keyframe that was successfully processed:

| Key | Meaning | Better |
|---|---|---|
| `psnr` | RGB peak signal-to-noise ratio from MSE, in dB | higher |
| `lpips` | Alex LPIPS from `torchmetrics` | lower |
| `ssim` | multi-scale SSIM, data range 1.0 | higher |
| `depth_l1_train_view` | mean absolute rendered-vs-GT depth error on each train/keyframe view | lower |
| `num_renders` | number of keyframe render evaluations included | context |

The source labels depth L1 here as `depth_l1_train_view` to distinguish it
from reconstruction `"depth l1"`. PSNR, LPIPS, and SSIM require CUDA images
and their respective metric dependencies. A zero MSE can make the raw PSNR
calculation non-finite; inspect the value rather than silently clamping it.
`rendering_metrics.png` plots per-render PSNR, SSIM, and train-view depth L1,
not LPIPS.

## Replica reconstruction metrics

The reconstruction path first integrates rendered submap views into a TSDF
mesh, translates the extracted mesh by the repository's fixed compensation
vector, writes `mesh/final_mesh.ply`, and cleans small connected components to
write `mesh/cleaned_mesh.ply`.

`reconstruction_metrics.json` merges the result returned by
`evaluate_3d_reconstruction` with the local 2-D result. The external 3-D
library controls the exact 3-D key names; the local invocation uses ICP
alignment and a `0.01` distance threshold. The local 2-D key is exactly:

```json
{"depth l1": 1.23}
```

The code multiplies the sampled depth difference by 100, so with meter-scale
Replica data this is conventionally read as centimeters. It samples up to
1,000 random unseen-area camera views, filters zero reconstructed depth, and
uses headless Open3D to compare rendered depths. `depth l1` may be `null` when
the 2-D attempt fails even though the 3-D metric was produced. It is absent
when mesh construction or the 3-D evaluator fails before the result is
written.

Reconstruction is skipped—not failed—for any dataset name other than the
literal `replica`. It needs both Replica cull assets and the
`evaluate_3d_reconstruction` dependency. A full GUI desktop is not the
requirement; headless Open3D is.

## Global-map outputs and NVS

`<scene>_global_map.ply` is the refined Gaussian PLY after submap point merge,
statistical filtering, and 10,000 color/depth refinement iterations. Its
presence indicates that map refinement returned and `save_ply` ran; it does
not certify trajectory or rendering quality.

For the literal `scannetpp` dataset name, the evaluator writes one JPEG per
test frame at `nvs_eval/0000.jpg`, etc. NVS PSNR is computed against test
colors and printed as a per-frame `PSNR List` and `Avg. NVS PSNR`. There is no
NVS JSON output in the current implementation. For all other dataset names,
map PLY creation is still attempted but NVS is intentionally not run.

## Partial-result policy

`Evaluator.run()` catches exceptions independently around trajectory,
rendering, reconstruction, and global-map stages. Therefore report one of
`complete`, `partial`, `skipped-by-dataset`, or `failed` per stage. A JSON file
left by a previous run is not evidence that the current invocation completed.
