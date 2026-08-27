---
name: motion-retargeting
description: "Routes Mixamo or custom BVH preparation, intra- and
  cross-structural retargeting, pretrained evaluation, training, kinematics, and
  output validation for Deep Motion Editing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Motion retargeting

Use this route when a task moves a motion BVH onto another supported skeleton,
prepares Mixamo/custom training data, evaluates the supplied pretrained model,
or trains the skeleton-aware retargeting model. This is a script-oriented
repository, not an installed package: run upstream commands from its
`retargeting/` directory, or use the bundled safe command builders below.

## Route quickly

- **Inspect a BVH, pair, or dataset first**: run
  [`scripts/validate_retargeting_data.py`](scripts/validate_retargeting_data.py).
  It is standalone, read-only, and does not import the legacy source modules.
- **One input/target pair**: read
  [`references/workflows.md`](references/workflows.md), then use
  [`scripts/run_retargeting.py`](scripts/run_retargeting.py) to preflight and
  construct the `eval_single_pair.py` command.
- **Canned demos or quantitative evaluation**: use the same helper with
  `--workflow demo|eval|test`; read the output and cleanup warnings first.
- **Train from scratch**: follow
  [`references/data-preparation.md`](references/data-preparation.md), then use
  [`scripts/run_training.py`](scripts/run_training.py). Training is never
  implicit; the helper is dry-run by default.
- **Model/kinematics details**: consult
  [`references/api-reference.md`](references/api-reference.md).
- **Failure diagnosis**: consult
  [`references/troubleshooting.md`](references/troubleshooting.md).

## Minimum input contract

1. A standard BVH has a hierarchy, unique joint names, a root, offsets,
   channels, a `MOTION` section, positive `Frame Time`, and complete motion
   rows. The bundled validator checks these textual invariants; it cannot
   replace the source parser's supported-skeleton classification.
2. For inference, the input and target paths must be existing `.bvh` files
   inside character-like directories. The model expects one of the skeleton
   types hard-coded in `retargeting/datasets/bvh_parser.py`, with the required
   end-effectors and compatible simplified topology. Same T-pose conventions
   are a dataset assumption, not inferred from filenames.
3. A pretrained run requires a user-supplied `save_dir` containing `para.txt`
   and both topology checkpoint trees at epoch `20000`; see the exact layout in
   [`references/data-preparation.md`](references/data-preparation.md). No
   checkpoint is bundled by this skill.
4. Use the shared BVH and kinematics contract in
   [`../animation-data/SKILL.md`](../animation-data/SKILL.md) before converting
   or comparing motions. Send FBX conversion, skinning, rendering, and Blender
   output to [`../blender-visualization/SKILL.md`](../blender-visualization/SKILL.md).

## Single-pair semantics

`eval_single_pair.py` requires `--input_bvh`, `--target_bvh`, `--test_type`,
and `--output_filename`; these have no source-parser defaults. `--test_type`
is exactly `intra` or `cross`:

- **intra** keeps the source motion topology and retargets to another
  character in the same structural group. The source code uses a fixed
  companion (`BigVegas` or `Goblin_m`) and character-name suffix logic, so
  character directory names and the standard-BVH inventory matter.
- **cross** builds two one-character groups and decodes the source latent with
  the target skeleton. This is the usual different-topology case; target
  character naming still determines the output writer.

The legacy `recover_space()` replaces every `_` with a space in all three
path arguments. Therefore `Dancing_Running_Man.bvh` is recovered as
`Dancing Running Man.bvh`, but a literal underscore cannot be represented.
The bundled runner encodes spaces and rejects underscores in its safe default;
`--path-mode literal` is only for a deliberately patched upstream script and
must not be executed against the unmodified source.

## Defaults that matter

From `retargeting/option_parser.py`, the important defaults are
`save_dir=./pretrained`, `cuda_device=cuda:0`, `window_size=64`,
`rotation=quaternion`, `dataset=Mixamo`, and `eval_seq=0`. The parser also
defaults `num_layers=2`, `batch_size=256`, `epoch_num=20001`,
`learning_rate=2e-4`, `normalization=1`, `pos_repr=3d`, and
`model=mul_top_mul_ske`. In evaluation, `eval.py` and
`eval_single_pair.py` force quaternion rotation and set `is_train=False`;
they use CPU when `torch.cuda.is_available()` is false, otherwise they request
the selected CUDA device. CPU is a valid fallback for small checks but CUDA is
recommended for full inference, evaluation, and training.

## Output and limits

A successful single-pair upstream run writes a target-character BVH under the
model's result staging area and copies it to `output_filename`; the runner
checks that the requested file exists and reparses its basic BVH structure.
The demo additionally writes `input.bvh`, `gt.bvh`, and applies the source
foot-contact fixer to `result.bvh`. Batch `eval.py` writes results under
`save_dir/results/bvh`; `test.py` collects intra/cross errors and then removes
that generated `results/bvh` directory. Keep quantitative runs explicit and
back up results before allowing `test.py`.

Preprocessing, FBX conversion, downloads, full evaluation, and training can be
large, external-data, Blender-, or GPU-dependent. The bundled helpers only
validate and construct commands unless `--run` is supplied. They do not
install packages, download Mixamo data, copy checkpoints, or train by default.
