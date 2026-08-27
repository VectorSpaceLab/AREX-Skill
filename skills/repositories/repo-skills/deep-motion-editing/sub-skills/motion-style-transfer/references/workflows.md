# Style-transfer workflows

This reference records source behavior. Commands execute in a user-supplied
checkout, not in this generated skill. Prefer the bundled helpers: they use
argv, are dry-run by default, and do not acquire external data.

## Pretrained inference

The source command is:

```bash
python style_transfer/test.py --name pretrained --batch_size 1 --config config \
  --content_src /data/content.bvh --style_src /data/style.bvh \
  --output_dir /results/style-a
```

`test.py` accepts exactly these options:

| Option | Actual behavior |
|---|---|
| `--name` | String. If present, replaces class default `pretrained`; it changes the experiment directory and therefore checkpoint lookup. |
| `--batch_size` | Integer parser option. Inference uses `to_batch=True` and does not need a configurable batch; `Config.initialize` has a source typo and only assigns this field when `args.name is not None`. |
| `--config` | Config module name, default `config`; imported with `importlib.import_module`, then `<config>.py` is copied to `info` when saving. |
| `--content_src` | Parser default is `None`, but the actual path is always sent to `process_single_bvh`; an existing compatible BVH is required. |
| `--style_src` | Parser default is `None`; a lowercase `.bvh` suffix chooses 3D, otherwise the path is treated as a JSON directory. |
| `--output_dir` | Parser default is `None`; source uses `<main_dir>/test_output` when omitted. |

The source constructs `Config`, calls `initialize`, creates `Trainer`, moves it
to `config.device`, calls `resume`, processes content/style, calls
`Trainer.test`, and saves two files. The model output dictionary contains
`content_meta`, `style_meta`, `foot_contact`, `content`, `recon`, and `trans`;
`style` is 3D raw style content in the 3D branch or raw 2D style projection in
the JSON branch. `trans[0]` is passed to `save_bvh_from_network_output` as
`raw.bvh`. The same motion and `foot_contact[0]` go to `remove_fs` for
`fixed.bvh`.

A typical safe command-builder invocation is:

```bash
python sub-skills/motion-style-transfer/scripts/run_style_transfer.py \
  --source-root /path/to/deep-motion-editing \
  --content-src /data/content.bvh --style-src /data/style.bvh \
  --output-dir /results/style-a \
  --checkpoint-dir /path/to/deep-motion-editing/style_transfer/pretrained/pth \
  --normalization-dir /path/to/deep-motion-editing/style_transfer/data/xia_norms
```

The helper requires the output parent to already exist and refuses existing
`raw.bvh`/`fixed.bvh` unless `--allow-overwrite-output` is supplied. It checks
checkpoint files and the `mean`/`std` archive keys without importing PyTorch.
It does not create output directories in dry-run mode. `--execute` invokes the
user checkout only after these checks.

## Branch behavior: 3D versus OpenPose JSON

The branch condition is exactly equivalent to:

```python
if args.style_src.endswith('.bvh'):
    status = '3d'
    st_data = process_single_bvh(args.style_src, config, to_batch=True)
else:
    status = '2d'
    st_data = process_single_json(args.style_src, config, to_batch=True)
```

This check is lowercase and suffix-based. `STYLE.BVH` does not select 3D. A
3D style directory does not select 3D. Every non-`.bvh` path must be an
OpenPose frame directory that the source can parse. Content is always loaded
as BVH in both branches.

For 3D style, `process_single_bvh` uses `downsample=4`, `trim_scale=4`,
computes foot contact, content rotations/root channels, and 3D position style
channels. It loads `train_content.npz` and `train_style3d.npz` from
`config.extra_data_dir`. For JSON style, `process_single_json` calls
`AnimationData2D.from_openpose_json(scale=0.07, smooth=True)` and normalizes
42-channel style with the source-relative default
`style_transfer/data/treadmill_norm/test2d.npz`. The CLI has no argument for
that 2D normalization path.

## Xia/BFA dataset preparation

README's documented source sequence is:

```bash
cd style_transfer/data_proc
sh gen_dataset.sh
```

The shell file runs two commands, each with `window=32` and `window_step=8`:

```bash
python export_train.py --dataset xia --bvh_path ../data/mocap_xia \
  --output_path ../data/xia --window 32 --window_step 8 \
  --dataset_config ../global_info/xia_dataset.yml
python export_train.py --dataset bfa --bvh_path ../data/mocap_bfa \
  --output_path ../data/bfa --window 32 --window_step 8 \
  --dataset_config ../global_info/bfa_dataset.yml
```

`export_train.py` parser defaults are `--dataset xia`, `--bvh_path styletransfer`,
`--output_path xia_data`, `--window 48`, `--window_step 8`, and
`--dataset_config ../global_info/xia_dataset.yml`. Its active functions use
`downsample=4` internally. The bundled helper exposes explicit source root,
BVH path, output prefix, dataset, YAML, window, and step, and never runs both
datasets implicitly.

The exporter excludes only a file named exactly `rest.bvh`, reads the CMU
skeleton, converts each BVH to full motion plus a phase column, divides clips,
and stores compressed object-valued NPZ data. It writes `<prefix>.npz` and
`<prefix>.info`. Xia also creates `<prefix>_test` and copies selected test
BVHs. The helper refuses existing output artifacts unless overwrite is
explicit, but does not copy or inspect large source data during dry-run.

### Xia partition

Xia filenames must split into exactly `style`, integer content index, and a
suffix: `<style>_<content-index>_<suffix>.bvh`. The YAML's
`content_full_names` maps the index to a content family; `content_names` and
`content_test_cnt` control metadata and held-out clip counts. For each
content/style pair, the first configured number of unwindowed clips becomes
test. Other clips contribute overlapping train windows; trainfull retains
unwindowed clips. A non-divided clip is rounded to a multiple of four, has a
minimum target length of 12, and is reflection-padded if short.

### BFA partition

BFA filenames must split into exactly `<style>_<suffix>.bvh`. The exporter
reserves a final `2 * window` test clip from each complete group of ten such
windows when available, then emits training and trainfull windows from the
preceding material. BFA has 16 configured style labels and has no Xia content
family mapping. Empty or undersized subsets can fail later when the exporter
assembles metadata; preflight enough varied files before a full run.

## Archive/training sequence

Each `.npz` has `train`, `test`, and `trainfull` object entries. A subset is a
dictionary with `motion`, integer `style`, and `meta`; metadata includes style,
phase, and Xia content labels. The `.info` YAML stores counts/distributions
and Xia test filenames. NumPy loads this object data with `allow_pickle=True`.
It is not a model checkpoint.

After preparation, use:

```bash
python style_transfer/train.py --name xia-run --batch_size 128 --config config
```

`train.sh` only runs `python style_transfer/train.py`. Training creates six
loaders, `Trainer`, `info/info-network`, TensorBoardX writers under `log`, and
loops to `config.max_iter` (default 300000). It saves generator,
discriminator, and optimizer files at `save_freq` (default 50000). Training
alternates 3D and 2D style branches and uses the shared content encoder,
separate style encoders, AdaIN decoder, and class-conditional patch
 discriminator described by the source modules.

`Trainer.resume` selects the lexicographically last regular filename containing
`gen` and `.pt`; it then expects a discriminator file and `optimizer.pt` in the
same `model_dir`. A complete set is loaded with `map_location=config.device`,
optimizer states and schedulers are restored, and the iteration is parsed from
the generator filename. If no generator exists, it prints `Initialize from 0`;
that is not a pretrained result.

The bundled training helper checks the source-derived data, normalization, and
checkpoint paths, rejects partial checkpoint sets, requires explicit
`--allow-resume` for a complete set, and prints the source command. `--execute`
is required to begin training. It does not install TensorBoardX, alter config,
or shorten max iterations.

## Probes and plotting

`plot_demo_figures.sh` calls `style_transfer/probe/plot_clusters.py`. That
probe accepts `--name`, `--batch_size`, and `--config`, but its `main` always
calls `plot_demo`; it expects a completed run and generates cached code arrays
and figures. `anim_view.py` loads saved torch output with `--file` and can
interactively display or save animation. `latent_plot_utils.py` imports
Matplotlib, scikit-learn PCA/TSNE, and `tikzplotlib`; output may include PNG,
TikZ, cached NPZ, and TensorBoard figures. Missing these optional packages can
block `train.py` at import time because the source imports probe utilities
before `main`. These paths are reference-only, not inference acceptance gates.

## Foot-skate cleanup semantics

`remove_fs.remove_fs` receives network motion and a `[T,4]` foot-contact mask.
It converts the network representation, estimates a soft floor from four foot
joints, pins contact runs, interpolates nearby non-contact frames with
`interp_length=5`, then performs ten-iteration Jacobian inverse kinematics
with damping 4.0 before writing BVH. `force_on_floor=True` by default. Its
standalone CLI instead accepts `--data` (default `bla_3d`), creates
`<data>_bvh`, and batch-writes files; the helper deliberately does not bundle
or invoke that unsafe/legacy launcher. Inspect and render the generated files
through the adjacent skills.
