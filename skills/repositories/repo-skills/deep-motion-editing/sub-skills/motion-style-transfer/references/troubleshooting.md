# Troubleshooting and explicit limits

## Input and branch failures

| Symptom | Cause | Action |
|---|---|---|
| Content path is rejected | Content is not an existing lowercase `.bvh`; source always calls `process_single_bvh`. | Supply a compatible BVH or route conversion/retargeting first. |
| BVH style is parsed as JSON | Source checks `endswith('.bvh')` case-sensitively. | Use a lowercase `.bvh` filename for 3D; `STYLE.BVH` does not select it. |
| JSON directory fails on an unrelated file | Source opens every sorted directory entry and does not filter `.json`. | Keep only source-compatible frame JSON files. |
| `people`/keypoint `KeyError` | OpenPose schema lacks one required array. | Provide `people[0]` with `pose_keypoints_2d`, `hand_left_keypoints_2d`, and `hand_right_keypoints_2d`. |
| Empty sequence or index error | No detected person, insufficient body/hand points, or wrong OpenPose order. | Ensure at least one valid person and the evidenced body+hands layout; body-only arbitrary OpenPose is unsupported. |
| Style shape or model channel error | Skeleton/topology or projection shape differs. | Validate BVH against the CMU rest skeleton; use 64 3D-style or 42 2D-style channels. |

## Norm/config failures

| Symptom | Cause | Action |
|---|---|---|
| Missing `train_content.npz`/`train_style3d.npz` | 3D inference norms are absent under `extra_data_dir`. | Generate compatible norms from the same data/config; do not guess/pad arrays. |
| Missing `mean` or `std` | Archive key/schema is wrong. | Recreate a NumPy archive containing both keys and correct channel count. |
| JSON cannot find `test2d.npz` | JSON style uses a separate source-relative hard-coded path. | Place a compatible user-owned file at that expected location or intentionally adapt the source loader. |
| NaN/unstable output | Wrong norms, zero/near-zero std, mismatched skeleton, or incompatible weights. | Check archive values and source data provenance; regenerate as a set. |
| `--name` finds no weights | Name changes `<style_transfer>/<name>/pth`. | Use the experiment owning the weights; verify all three checkpoint components. |
| Config imports then copy fails | `initialize(save=True)` also copies `<config>.py` below source `style_transfer`. | Use a config file present in the source layout, not merely an importable module. |
| BFA labels/index failure | Default config has 8 Xia classes but BFA defines 16. | Use `bfa.npz`, 16 classes, compatible norms, and a 16-class checkpoint. |
| `--batch_size` ignored | Source setter tests `args.name` in its batch condition. | Pass a nonempty name; for inference batch size is effectively one. |

## Checkpoint/backend/import failures

- `Initialize from 0` means no generator checkpoint matched. It is an
  uninitialized model, not successful pretrained inference.
- A generator without discriminator and `optimizer.pt` is a partial resume and
  should be rejected. Lexicographic latest-file selection can choose an
  unexpected backup if filenames contain `gen`/`dis`; retain source's padded
  `gen_%08d.pt`/`dis_%08d.pt` naming.
- A state-dict mismatch means config architecture, class count, skeleton, or
  checkpoint is inconsistent. Do not force-load or silently ignore keys.
- CUDA visibility does not guarantee a usable driver/device. Verify the
  PyTorch/CUDA installation or use CPU deliberately; CPU can be very slow and
  is not a full performance validation.
- `ModuleNotFoundError` for `model`, `utils`, or siblings reflects the source's
  short-import/sys.path assumptions. Run from the explicit source root via the
  helper; this project has no install metadata.
- Modern NumPy may fail before style-transfer code loads with
  `ModuleNotFoundError: numpy.core.umath_tests`, imported by legacy shared
  `utils/Animation.py` through `utils/BVH.py`. This is a source compatibility
  blocker, not a missing checkpoint. Use the repository-approved compatibility
  fix or a maintained shared BVH implementation; do not silently vendor a
  patch in this sub-skill.
- A source environment without `tensorboardX` fails `train.py` at import time
  before configuration validation. Install it in the user environment or keep
  to read-only helper checks; the helper does not install packages.

## Training/probe dependencies

`train.py` imports `tensorboardX.SummaryWriter` and
`probe.latent_plot_utils` before entering `main`. The probe imports Matplotlib,
scikit-learn PCA/TSNE, and `tikzplotlib`. Missing one can block an otherwise
valid training startup. Install dependencies in a user-controlled environment
or adapt imports; the helper does not install packages or use network access.

`plot_clusters.py` expects completed run data/checkpoints and can write cached
NPZ, PNG, TikZ, and TensorBoard figures. `anim_view.py` is interactive unless
saving with Matplotlib/FFmpeg. Missing FFmpeg affects optional video export,
not the core test path. Plot/probe output is not a pretrained inference gate.

## Dataset/export failures

- `rest.bvh` is excluded only by exact filename; do not use it as a sample.
- Xia exporter expects exactly `<style>_<content-index>_<suffix>.bvh` and a
  positive content index known by `xia_dataset.yml`.
- BFA exporter expects exactly `<style>_<suffix>.bvh` and a label from its YAML.
- Empty train/test/trainfull input can fail when metadata is assembled. Start
  with enough files for each requested partition.
- Short clips are reflection-padded by design. Window/step values are temporal
  assumptions, not harmless metadata; regenerate archives and norms together
  after changing them.
- Full export parses BVH, performs kinematics, serializes object NPZ, and may
  copy Xia test BVHs. It can be slow and disk-heavy. Helpers do no bulk data
  copy/download by default and only execute with explicit `--execute`.

## Output/cleanup and non-goals

`raw.bvh` is direct network output. `fixed.bvh` is a separate result after
floor/contact correction, interpolation, and ten-iteration Jacobian IK. If
only raw exists, investigate cleanup; never relabel it fixed. The standalone
`remove_fs.py --data` launcher is not bundled because it assumes legacy paths,
creates `<data>_bvh`, and writes batches of files. Use the adjacent animation
skill for safe BVH checks.

This sub-skill does not promise automatic dataset/checkpoint/OpenPose download,
arbitrary skeletons, multi-person tracking, body-only OpenPose, uppercase
`.BVH` branch selection, full benchmark recovery, full training verification,
plot support, or GPU-throughput equivalence. It does not make the original
source checkout a hidden dependency: execution requires an explicit compatible
user-supplied source tree only when the user opts into the source command.
