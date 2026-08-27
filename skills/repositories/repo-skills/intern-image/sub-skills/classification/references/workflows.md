# Classification workflows

Evidence labels distilled into this reference: `classification/README.md`, `classification/main.py`, `classification/main_deepspeed.py`, `classification/main_accelerate.py`, `classification/train_in1k.sh`, `classification/train_in1k_deepspeed.sh`, `classification/train_inat18.sh`, `classification/extract_feature.py`, `classification/export.py`, and classification model/config source evidence.

This reference is self-contained for routine operation. Use the bundled `scripts/build_classification_command.py` to print copy/edit command templates; do not depend on the original shell launchers for command structure.

## Required runtime inputs

Before building a command, identify:

- `INTERNIMAGE_REPO`: a local InternImage checkout or installed source tree that contains the classification entry points.
- `config`: one classification YAML label such as `configs/internimage_b_1k_224.yaml`, `configs/without_lr_decay/internimage_b_1k_224.yaml`, or `configs/inaturalist2018/internimage_h_22ktoinat18_384.yaml`.
- `data_path`: dataset root for the selected `DATA.DATASET`.
- `checkpoint` or `pretrained`: `--resume` is used for evaluation/resume; `--pretrained` is used to initialize training from a pretrained weight.
- `launcher`: source workflows use `python -m torch.distributed.launch` for local distributed jobs or Slurm `srun` for cluster jobs. The local `main.py` requires a distributed launch context and a `--local-rank` value.
- GPU/backend readiness: real model execution requires PyTorch, CUDA, DCNv3/operator availability or an intentional fallback plan, and task dependencies. The generated helper only prints templates.

## Data layouts and dataset names

| Scenario | `--dataset` / config value | Data root expectation | Notes |
| --- | --- | --- | --- |
| Standard ImageNet-1K folders | `imagenet` | `DATA.DATA_PATH/train/<class>/*` and `DATA.DATA_PATH/val/<class>/*` | This is the safest layout for evaluation/training templates. Validation images must be moved into class subfolders. |
| Zipped ImageNet-1K | `imagenet` with `--zip` | root containing train/val zip files and matching map text files | The source docs describe `train.zip`, `val.zip`, `train_map.txt`, `val_map.txt` plus metadata examples. This path is not runtime-verified by this skill; prefer folder layout unless the user's package version and maps are known. |
| ImageNet-22K pretraining or 22K validation flow | `imagenet22K` | a 22K root containing class folders such as `fall11_whole` plus split metadata expected by the package | Source code sets 21,841 training classes and treats validation as a 1K mapping path. Dataset acquisition is out of scope. |
| iNaturalist 2018 | `inat18` | root containing iNat JSON metadata and image folders, including `train2018.json`, `val2018.json`, location JSON files, `test2018`, and `val2018` | Uses `intern_image_meta_former` configs and adds temporal/spatial metadata to each sample; class count is 8,142. |

## Command builder modes

Run from the generated classification sub-skill directory, or pass the script path explicitly from anywhere:

```bash
python scripts/build_classification_command.py --help
```

Supported modes:

| Mode | Prints | Important options |
| --- | --- | --- |
| `eval` | distributed `main.py --eval` template | `--config`, `--checkpoint`, `--data-path`, `--gpus`, `--launcher`, `--cfg-option` |
| `train` | distributed `main.py` training template | `--pretrained` for initialization, `--resume` for continuing, `--batch-size`, `--accumulation-steps`, `--use-checkpoint` |
| `throughput` | distributed `main.py --throughput` template | requires validation data and usually a checkpoint through `--checkpoint` |
| `deepspeed` | `main_deepspeed.py` template | `--zero-stage` supports stages 1 or 2 in source parser; use `accelerate` mode for ZeRO-3 |
| `accelerate` | `accelerate launch ... main_accelerate.py` template | `--accelerate-config`, `--logger`, `--accumulation-steps`; ZeRO-3/offload comes from the Accelerate YAML/DeepSpeed JSON |
| `extract-features` | `extract_feature.py` template | `--image`, `--keys`, `--checkpoint`, optional `--save-features` |
| `hf-transformers` | standalone Transformers Python heredoc | `--hf-model`, `--hf-task`, `--image`; no InternImage checkout import |

## Evaluation

Use `eval` for ImageNet or iNaturalist checkpoint evaluation. The source evaluation path loads `--resume`, builds the model from `--cfg`, constructs validation data, wraps the model in DistributedDataParallel, then reports top-1/top-5 accuracy.

```bash
python scripts/build_classification_command.py \
  --mode eval \
  --config configs/internimage_b_1k_224.yaml \
  --checkpoint CHANGE_ME/internimage_b_1k_224.pth \
  --data-path CHANGE_ME/imagenet \
  --gpus 1 \
  --master-port 12345
```

For iNaturalist evaluation, use the iNaturalist config and data root:

```bash
python scripts/build_classification_command.py \
  --mode eval \
  --config configs/inaturalist2018/internimage_h_22ktoinat18_384.yaml \
  --dataset inat18 \
  --checkpoint CHANGE_ME/internimage_h_22ktoinat18_384.pth \
  --data-path CHANGE_ME/inat2018 \
  --gpus 8
```

## Training from scratch or fine-tuning

Use `train` for the standard `main.py` path. Source configs for reproduced paper results are under the `without_lr_decay` family. The source code linearly scales base/warmup/min learning rates by `per_gpu_batch_size * world_size / 512`, then scales again by `ACCUMULATION_STEPS` when accumulation is greater than one.

```bash
python scripts/build_classification_command.py \
  --mode train \
  --config configs/without_lr_decay/internimage_t_1k_224.yaml \
  --data-path CHANGE_ME/imagenet \
  --gpus 8 \
  --batch-size 512 \
  --output CHANGE_ME/work_dirs
```

Fine-tune from a 22K checkpoint by adding `--pretrained`:

```bash
python scripts/build_classification_command.py \
  --mode train \
  --config configs/internimage_l_22kto1k_384.yaml \
  --pretrained CHANGE_ME/internimage_l_22k_384.pth \
  --data-path CHANGE_ME/imagenet \
  --gpus 32 \
  --batch-size 16 \
  --accumulation-steps 1 \
  --use-checkpoint
```

Continue an interrupted PyTorch checkpoint by adding `--resume CHANGE_ME/checkpoint.pth`. For DeepSpeed checkpoint directories, see the DeepSpeed section below because source loading logic differs.

## Throughput

Throughput mode still builds the validation loader and calls CUDA operations. It is a GPU benchmark template, not a CPU smoke test:

```bash
python scripts/build_classification_command.py \
  --mode throughput \
  --config configs/internimage_t_1k_224.yaml \
  --checkpoint CHANGE_ME/internimage_t_1k_224.pth \
  --data-path CHANGE_ME/imagenet \
  --gpus 1
```

## Slurm launch form

The upstream shell launchers used Slurm `srun` with environment variables for GPU count, GPUs per node, CPU count, and optional extra Slurm arguments. The bundled builder can emit the same shape without copying cluster-specific defaults:

```bash
python scripts/build_classification_command.py \
  --mode train \
  --launcher srun \
  --partition CHANGE_ME_PARTITION \
  --job-name internimage_t_train \
  --gpus 8 \
  --gpus-per-node 8 \
  --config configs/internimage_t_1k_224.yaml \
  --data-path CHANGE_ME/imagenet \
  --batch-size 512 \
  --srun-arg=--quotatype=reserved
```

If a site does not support a source-documented Slurm option such as `--quotatype`, omit it. Use `--srun-arg=VALUE` only for scheduler flags approved in the user's cluster, especially when the value begins with `-`.

## DeepSpeed

Source evidence supports DeepSpeed to reduce memory cost on large InternImage-H/G style models. Install and configure DeepSpeed in the user's environment before running. The source `main_deepspeed.py` builds a DeepSpeed config in Python with AdamW, fp16, gradient clipping, and gradient accumulation.

Important source discrepancy: the prose examples include `--zero-stage 3` for the plain DeepSpeed launcher, but the actual `main_deepspeed.py` parser only accepts `--zero-stage 1` or `2` and comments that ZeRO-3 should use the Accelerate integration. For ZeRO-3 or CPU offload, prefer `accelerate` mode.

```bash
python scripts/build_classification_command.py \
  --mode deepspeed \
  --config configs/internimage_h_22kto1k_640.yaml \
  --pretrained CHANGE_ME/internimage_h_jointto22k_384.pth \
  --data-path CHANGE_ME/imagenet \
  --gpus 8 \
  --batch-size 16 \
  --accumulation-steps 4 \
  --zero-stage 2
```

For DeepSpeed evaluation, pass `--eval --checkpoint CHANGE_ME/checkpoint_or_deepspeed_dir`. The source evaluation path first tries a normal PyTorch checkpoint, then tries DeepSpeed fp32 extraction, then falls back to loading `mp_rank_00_model_states.pt` from a checkpoint directory.

## Accelerate with DeepSpeed

The Accelerate path uses `accelerate launch --config_file ... main_accelerate.py`. Source configs include local 8-GPU DDP fp16, ZeRO-1, ZeRO-1 without loss scale, ZeRO-3 offload, and ZeRO-3 offload without loss scale. The source `main_accelerate.py` appends `_deepspeed` to `OUTPUT`, disables ZeroRedundancyOptimizer in the YACS config, and supports `--logger tensorboard|wandb`.

```bash
python scripts/build_classification_command.py \
  --mode accelerate \
  --accelerate-config configs/accelerate/dist_8gpus_zero3_offload.yaml \
  --config configs/internimage_h_22kto1k_640.yaml \
  --pretrained CHANGE_ME/internimage_h_jointto22k_384.pth \
  --data-path CHANGE_ME/imagenet \
  --batch-size 16 \
  --accumulation-steps 4 \
  --output CHANGE_ME/output_zero3_offload
```

## Intermediate feature extraction

`extract_feature.py` wraps a PyTorch module with forward hooks. Keys are nested module names such as `patch_embed`, `levels.0.downsample`, or `levels.0.blocks.0.dcn`. The source script loads `checkpoint['model']`, calls `.cuda()` on the model and input image, prints captured tensor shapes, and saves only when `--save` is present.

```bash
python scripts/build_classification_command.py \
  --mode extract-features \
  --config configs/internimage_t_1k_224.yaml \
  --checkpoint CHANGE_ME/internimage_t_1k_224.pth \
  --image CHANGE_ME/image.png \
  --keys patch_embed levels.0.downsample levels.0.blocks.0.dcn \
  --save-features
```

Known source behavior: when `--save` is used, the source script writes to a path derived from the image path by replacing the last three characters with `pth`; it does not expose a separate output path. Copy the generated command and adjust the image path carefully if the extension is not a three-character suffix such as `png` or `jpg`.

## Export routing

Classification export evidence comes from `classification/export.py`: `--model_name` selects `configs/<model_name>.yaml` and `<ckpt_dir>/<model_name>.pth`, ONNX export uses a dummy CUDA tensor with input/output names `input` and `output`, and TensorRT conversion uses mmdeploy TensorRT helpers plus the InternImage DCNv3 custom op.

For user export requests, collect these classification inputs and route to the deployment sub-skill:

- model name, for example `internimage_t_1k_224`;
- checkpoint directory containing `<model_name>.pth`;
- target format, ONNX or TensorRT;
- CUDA/TensorRT/mmdeploy/custom-op readiness.

Do not start a TensorRT or custom-op build from this classification sub-skill.
