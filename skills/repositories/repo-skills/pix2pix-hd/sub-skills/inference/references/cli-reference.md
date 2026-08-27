# pix2pixHD Inference CLI Reference

This reference focuses on the flags that matter for `test.py` and the helper scripts that build or preflight inference commands.

## Hard-coded test-time overrides in `test.py`

`test.py` forces these values before the loop starts:

- `nThreads = 1`
- `batchSize = 1`
- `serial_batches = True`
- `no_flip = True`

So the command line does **not** need to set them for standard inference.

## Core checkpoint and output flags

| Flag | Default | What it controls | Notes |
| --- | --- | --- | --- |
| `--name` | `label2city` | Experiment / checkpoint directory name | Must match the folder under `checkpoints_dir` |
| `--checkpoints_dir` | `./checkpoints` | Root of checkpoint lookup | The generator file is read from `<checkpoints_dir>/<name>/` |
| `--which_epoch` | `latest` | Checkpoint label suffix | `test.py` expects `<which_epoch>_net_G.pth` |
| `--phase` | `test` | Dataset phase and HTML folder name | Combined with `which_epoch` in the results path |
| `--results_dir` | `./results/` | HTML and image output root | Results are written to `<results_dir>/<name>/<phase>_<which_epoch>/` |
| `--how_many` | `50` | Maximum number of samples to process | The loop stops after this many items |
| `--gpu_ids` | `0` | CUDA device selection | Standard synthesis assumes a CUDA-capable GPU |

## Input and model-shape flags

| Flag | Default | What it controls | Notes |
| --- | --- | --- | --- |
| `--dataroot` | `./datasets/cityscapes/` | Dataset root | Builder scripts expand relative paths from `--repo-root` |
| `--label_nc` | `35` | Number of label channels | Set to `0` for RGB-to-RGB translation |
| `--no_instance` | off | Disable instance maps | If off, the model still expects `inst` inputs |
| `--netG` | `global` | Generator topology | Use `local` with `--ngf 32 --resize_or_crop none` for the 1024p recipe |
| `--ngf` | `64` | Generator width | Lowered to `32` in the 1024p recipe |
| `--resize_or_crop` | `scale_width` | Preprocessing mode | The 1024p recipe uses `none` |
| `--data_type` | `32` | Tensor dtype | `16` and `8` are accepted but are not the usual synthesis path |

## Feature-conditioning flags

| Flag | Default | What it controls | Notes |
| --- | --- | --- | --- |
| `--instance_feat` | off | Instance-wise feature conditioning | Used by the feature-conditioned recipes |
| `--label_feat` | off | Label-wise feature conditioning | Alternative feature route supported by the model |
| `--load_features` | off | Load precomputed feature maps from `phase_feat` | This is a feature-workflow path, not the plain label-only recipe |
| `--cluster_path` | `features_clustered_010.npy` | Clustered feature cache file | Resolved under `<checkpoints_dir>/<name>/` |
| `--use_encoded_image` | off | Encode the paired real image with `netE` | Meaningful only when the command is already feature-enabled |

## Optional export/runtime flags

| Flag | Default | What it controls | Notes |
| --- | --- | --- | --- |
| `--export_onnx` | unset | Export the model to ONNX and exit | The path must end in `.onnx` |
| `--engine` | unset | Run a serialized TensorRT engine | Reference-only path; see `accelerated-inference.md` |
| `--onnx` | unset | Run ONNX through TensorRT | Reference-only path; see `accelerated-inference.md` |

## Interaction rules

- `--export_onnx` is an export-only path. It exits after the first sample and does not continue to normal HTML synthesis.
- `--engine` and `--onnx` are both optional vendor paths. Do not combine them in a single run.
- `--cluster_path` matters for sampled feature inference, not plain label-only inference.
- `--use_encoded_image` is not a substitute for feature mode; it changes how the feature map is produced once feature mode is already enabled.
- `--load_features` expects precomputed feature-map folders and is usually paired with the feature workflow rather than the plain 512p/1024p recipes.
- `--results_dir` controls where HTML is written; `--checkpoints_dir` controls where the checkpoint is read from.

## Expected filesystem layout

| Item | Expected path |
| --- | --- |
| Generator checkpoint | `<checkpoints_dir>/<name>/<which_epoch>_net_G.pth` |
| Optional encoder checkpoint | `<checkpoints_dir>/<name>/<which_epoch>_net_E.pth` |
| Sampled feature cache | `<checkpoints_dir>/<name>/<cluster_path>` |
| HTML summary | `<results_dir>/<name>/<phase>_<which_epoch>/index.html` |
| Rendered images | `<results_dir>/<name>/<phase>_<which_epoch>/images/` |

## Helper-script contract

- `scripts/build_inference_command.py` accepts an explicit `--repo-root` and expands relative defaults from that checkout.
- `scripts/check_checkpoint.py` preflights the checkpoint path and any feature-cache path before a run starts.
- Neither helper should assume the current shell directory is the repository root.
