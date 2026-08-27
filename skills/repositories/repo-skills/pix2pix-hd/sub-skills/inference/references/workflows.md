# Inference Workflows

This reference distills the repo's test-time recipes into safe, explicit command plans that start from an assumed repo checkout but always resolve paths from an explicit `--repo-root`.

## Output anatomy

A successful standard inference run writes:

```text
<results_dir>/<name>/<phase>_<which_epoch>/
  index.html
  images/
    <input_basename>_input_label.jpg
    <input_basename>_synthesized_image.jpg
```

The HTML page is created by `util/html.py`; `util/visualizer.py` writes the images and builds the page content. The results directory is separate from `checkpoints_dir`.

## Checkpoint anatomy

The checkpointed generator is expected at:

```text
<checkpoints_dir>/<name>/<which_epoch>_net_G.pth
```

Feature-guided runs may also use:

```text
<checkpoints_dir>/<name>/<which_epoch>_net_E.pth
<checkpoints_dir>/<name>/<cluster_path>
```

`which_epoch` defaults to `latest`. `cluster_path` defaults to `features_clustered_010.npy` and is resolved under the experiment checkpoint directory.

## Canonical recipe table

| Workflow | Source recipe | Safe builder intent | Key flags | Expected result |
| --- | --- | --- | --- | --- |
| 512p labels only | `scripts/test_512p.sh` | Build a plain `test.py` command from an explicit repo root | `--name label2city_512p` | HTML under `results/label2city_512p/test_latest/` |
| 1024p labels only | `scripts/test_1024p.sh` | Build a local-enhancer `test.py` command | `--name label2city_1024p --netG local --ngf 32 --resize_or_crop none` | HTML under `results/label2city_1024p/test_latest/` |
| 512p feature-conditioned | `scripts/test_512p_feat.sh` | Build the feature-prep command, then the feature-enabled test command | `encode_features.py` then `--instance_feat` | Clustered features under `checkpoints/label2city_512p_feat/` and HTML under `results/label2city_512p_feat/test_latest/` |
| 1024p feature-conditioned | `scripts/test_1024p_feat.sh` | Build the local-enhancer feature-prep command, then the feature-enabled test command | `--netG local --ngf 32 --resize_or_crop none --instance_feat` | Clustered features under `checkpoints/label2city_1024p_feat/` and HTML under `results/label2city_1024p_feat/test_latest/` |
| Encoded-image feature inference | `models/pix2pixHD_model.py` + `AlignedDataset` | Keep a feature-enabled command and add `--use_encoded_image` | `--use_encoded_image` | Uses `netE` on paired real images instead of sampled cluster features |
| ONNX export | `test.py` | Emit an export-only command | `--export_onnx <file.onnx>` | Writes an ONNX file and exits after the first sample |
| TensorRT/ONNX runtime | `run_engine.py` | Reference-only optional path | `--engine <plan>` or `--onnx <model.onnx>` | Vendor-specific path; see the accelerated reference before relying on it |

## Builder usage

The helper script is meant to print commands, not execute them.

```bash
python scripts/build_inference_command.py --repo-root /path/to/pix2pixHD --recipe 1024p --how-many 5
python scripts/build_inference_command.py --repo-root /path/to/pix2pixHD --recipe 1024p-feat --include-feature-prep
python scripts/build_inference_command.py --repo-root /path/to/pix2pixHD --recipe 1024p --mode export-onnx --artifact-path artifacts/pix2pixhd.onnx
```

The builder resolves default `dataroot`, `checkpoints_dir`, and `results_dir` from `--repo-root` so the printed command can be copied into any shell session.

## Source-script adaptation notes

- `scripts/test_512p.sh` is the simplest baseline and becomes the default label-only recipe.
- `scripts/test_1024p.sh` adds the local generator flags required for the full-resolution model.
- `scripts/test_512p_feat.sh` and `scripts/test_1024p_feat.sh` both run `encode_features.py` before `test.py`.
- `scripts/test_1024p_feat.sh` in the source tree contains a legacy `---netG` typo; use `--netG` in any adapted command.
- The feature recipes assume the clustered `.npy` file has already been written to `checkpoints/<name>/`.

## Result-location reminders

- `--how_many` limits the number of samples processed; it does not change the output directory.
- `--results_dir` controls the root of the HTML tree, while `--checkpoints_dir` controls checkpoint lookup.
- `--phase` and `--which_epoch` are both part of the HTML directory name, so a `val` run will not land in the same folder as a `test` run.
- If `--use_encoded_image` is active, the dataset loader also needs the paired image folder convention from `setup-and-data`.
- If `--load_features` is active, the dataset loader expects the `phase_feat` folder used by the feature workflow.
