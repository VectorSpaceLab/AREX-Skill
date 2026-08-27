# Cross-cutting troubleshooting

## Import and dependency failures

1. Run the bundled environment checker before reinstalling anything.
2. Confirm `torch` and `torchvision` are a compatible pair and that the active
   Python is the one intended for DINO.
3. Install `requirements.txt` in an isolated environment, then run `python -m
   pip check`.
4. `pycocotools` is required by the COCO instance loader. If the repository's
   Git source fails because generated C sources are missing, use a compatible
   published wheel and record the substitution. `panopticapi` is only needed
   for panoptic/mask paths.
5. `timm` is needed by the Swin/ConvNeXt backbone modules even when the default
   ResNet route is selected.

## CUDA operator failures

`MultiScaleDeformableAttention` is not a pure-Python optional convenience: the
standard DINO deformable encoder/decoder imports it. If import fails, stop and
use the setup route. For a source build, verify a CUDA-enabled PyTorch,
`CUDA_HOME`, `nvcc`, a supported host compiler, CUDA development headers, and
an architecture matching the target GPU. CUDA 12 builds may need the active
CCCL/Thrust include directory. Rebuild after changing the torch, toolkit,
compiler, or architecture combination; do not reuse an old binary silently.

A `cannot find -lcudart` linker error means the linker cannot see the CUDA
runtime library, not that the Python package is necessarily broken. A missing
`cusparse.h`, `thrust/complex.h`, or `nv/target` is an include-path/toolkit
mismatch. A compiler rejection for a GCC version above the toolkit's supported
range requires a compatible GCC, not just an `--allow-unsupported-compiler`
flag. A CUDA OOM during a tiny smoke can mean the visible device is occupied;
select a free device and preserve the occupancy warning.

## Dataset and config failures

The loader expects `train2017/`, `val2017/`, and
`annotations/instances_{train,val}2017.json` for ordinary train/eval setup.
The current `main.py` constructs both train and validation datasets before its
`--eval` branch, so an evaluation can fail because the train side is absent.
Run the read-only COCO validator and fix the input layout outside this skill.
Do not enable the repository's optional data-copy path: it can remove and
recreate paths.

`SLConfig` executes Python config files and recursively resolves `_base_`.
Use `--options key=value` only for config keys; parser flags such as
`--coco_path`, `--resume`, and `--output_dir` belong outside `--options`.
Reject duplicate or misspelled options instead of assuming they were applied.

## Checkpoint and workflow failures

A strict checkpoint load failure usually means scale, backbone, class count,
EMA/model key, or config mismatch. Inspect the checkpoint keys and pair the
config before changing `strict` behavior. Use `--resume` for a full state and
`--pretrain_model_path` plus explicit `--finetune_ignore` for partial
fine-tuning; never pass both.

An evaluation log is not a benchmark result until the config, checkpoint,
data split, device, command, and COCO evaluator output are recorded. A
GFLOPS/FPS benchmark does not load a checkpoint and says nothing about AP.
Submitit importability does not prove that Slurm, a shared folder, or cluster
permissions exist.
