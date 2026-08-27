---
name: motion-style-transfer
description: "Route pretrained 3D-to-3D and OpenPose JSON-to-3D motion style
  transfer, Xia/BFA dataset preparation, normalization, configuration, training,
  probing, and raw/fixed BVH artifact handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Motion style transfer

Use this sub-skill when a compatible CMU-style BVH content motion should receive
style from a 3D BVH or from OpenPose frame JSON, when the Xia/BFA training
archive must be prepared, or when a style-transfer run/checkpoint needs
inspection. The source repository is script-oriented and has no package
metadata or console entry point. The bundled helpers validate and build safe
commands; they do not contain downloaded data, weights, or source imports.

## Route by task

- **Pretrained inference:** read [workflows.md](references/workflows.md) and
  use [run_style_transfer.py](scripts/run_style_transfer.py). Content is always
  a BVH. A lowercase `.bvh` style selects 3D; every other style path selects
  the OpenPose JSON-directory branch.
- **Xia/BFA preparation:** read [data-formats.md](references/data-formats.md)
  and use [prepare_style_dataset.py](scripts/prepare_style_dataset.py). The
  helper emits the source exporter command and runs it only with `--execute`.
- **Training/resume:** read [configuration.md](references/configuration.md)
  and use [run_training.py](scripts/run_training.py). It is a long-running,
  artifact-producing operation and is dry-run by default.
- **Probe/plotting:** treat `probe/*.py` and `plot_demo_figures.sh` as optional
  reference-only analysis. Read the dependency and output limits in
  [workflows.md](references/workflows.md).

## Inference contract

Required logical inputs are an explicit user-owned source checkout, existing
content BVH, existing style BVH or JSON directory, output directory, complete
checkpoint directory, and normalization archives. The source CLI options are
exactly `--name`, `--batch_size`, `--config`, `--content_src`, `--style_src`,
and `--output_dir`. `--config` defaults to `config`; `--output_dir` otherwise
defaults to `<main_dir>/test_output`; the parser does not expose checkpoint or
normalization paths. The helper therefore requires those paths explicitly and
checks them against the source config's derived layout.

A safe first pass is:

```bash
python /path/to/motion-style-transfer/scripts/run_style_transfer.py \
  --source-root /path/to/deep-motion-editing \
  --content-src /data/content.bvh --style-src /data/style.bvh \
  --output-dir /results/style-a \
  --checkpoint-dir /path/to/deep-motion-editing/style_transfer/pretrained/pth \
  --normalization-dir /path/to/deep-motion-editing/style_transfer/data/xia_norms
```

The helper prints an argv-safe command and performs no model import or write by
default. Add `--execute` only after checking the branch, checkpoint, norms, and
output policy. For JSON style, the source additionally requires its
source-relative `data/treadmill_norm/test2d.npz`; the unmodified source CLI
cannot override this path.

The source test path calls `process_single_bvh(content_src, ..., to_batch=True)`.
It calls `process_single_bvh` for a style path ending in lowercase `.bvh`, and
`process_single_json` otherwise. `Trainer.test` returns transformed motion and
content foot-contact channels. The source writes `raw.bvh`, then foot-skate
cleanup writes `fixed.bvh`; these are separate artifacts. Accept inference only
when the process succeeds, both files exist, and shared BVH/skeleton validation
passes. Use `raw.bvh` to diagnose the network and `fixed.bvh` to diagnose cleanup.

## Data/runtime assumptions

BVHs must use the standard CMU-derived 31-joint skeleton and compatible axes,
quaternion ordering, rest skeleton, and topology. Single-BVH processing is
hard-coded to downsample by four. Content and 3D style require
`train_content.npz` and `train_style3d.npz`; each archive needs `mean` and
`std`. OpenPose style is a 42-channel projection normalized by the source's
hard-coded `test2d.npz`. See [data-formats.md](references/data-formats.md) for
actual channel shapes and the evidenced OpenPose schema.

`Config.initialize` creates `main_dir`, `pth`, `log`, `info`, and `output`
under the experiment name, and selects `cuda:0` when CUDA is available or CPU
otherwise. CPU fallback is not a throughput or quality equivalence claim.
Training also imports TensorBoardX and probe plotting dependencies at module
startup. Missing optional plotting packages can therefore block the unmodified
training entry point even though plotting is not needed conceptually for
inference; see [troubleshooting.md](references/troubleshooting.md).

## Training/data guardrails

The normal sequence is: obtain user-owned Xia/BFA BVHs, dry-run and execute
preparation, verify archive/classes/norms, dry-run training, then explicitly
start the source trainer. Source defaults are `window=32`, `window_step=8` in
`gen_dataset.sh`, while the exporter parser defaults to window 48 and step 8.
The default config is Xia (`xia.npz`, 8 classes); BFA has 16 classes and needs a
matching config/checkpoint/norm set. Do not mix these archives or labels.

The source trainer defaults to 300000 iterations, writes checkpoints/logs/info/
probe artifacts, and auto-resumes from a complete `gen*.pt`, `dis*.pt`, and
`optimizer.pt` set under `<style_transfer>/<name>/pth`. The training helper
requires `--allow-resume` for an existing complete set and rejects partial
sets. It never downloads data, copies checkpoints, removes files, or silently
shortens training.

## Adjacent routes

- Use [../animation-data/SKILL.md](../animation-data/SKILL.md) for shared BVH
  parsing/writing, skeleton validation, foot contact, and cleanup inspection.
- Route arbitrary-skeleton preparation/retargeting to
  [../motion-retargeting/SKILL.md](../motion-retargeting/SKILL.md) before style
  transfer; this sub-skill does not retarget arbitrary skeletons.
- Route rendered `raw.bvh`/`fixed.bvh` to the `blender-visualization` sibling
  through the root router when that sibling is present; Blender is a separate
  runtime.

## Source-to-bundle decisions

`test.py`, `data_loader.py`, `config.py`, `model.py`, `networks.py`, and
`trainer.py` are distilled evidence, not bundled runtime modules. `demo.sh` is
replaced by the parameterized inference helper. `export_train.py` and
`gen_dataset.sh` are represented by the safe preparation helper. `train.py` and
`train.sh` are represented by the safe training helper. `remove_fs.py` is
represented as documented callable cleanup behavior, not its legacy batch
launcher. `probe/*.py` and plotting shell commands remain reference-only due to
optional dependencies, interactive behavior, and potentially large outputs.

All three helpers expose `--help`, validate before source execution, use argv
rather than shell interpolation, and are safe/dry-run by default. Their
`--source-root` is an explicit downstream runtime input; it is not a link to
this generated skill or to a private production checkout.
