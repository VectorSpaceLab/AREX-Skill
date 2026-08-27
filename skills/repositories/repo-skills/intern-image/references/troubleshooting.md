# InternImage Cross-Cutting Troubleshooting

## Purpose

Use this for failures that span multiple InternImage workflows: environment setup, imports, DCNv3/CUDA, OpenMMLab versioning, checkpoint/config pairing, data roots, distributed launch, and optional export dependencies. For task-specific flags and examples, route to the relevant sub-skill.

## Fast diagnosis

Run the bundled environment checker from this skill directory:

```bash
python scripts/check_internimage_environment.py --profile classification --profile detection --profile segmentation --profile deployment
```

Use `--json` if another tool will consume the results. The checker imports modules only when safe, probes Python/tool availability, reports CUDA/TensorRT signals, and does not train, download, or build.

## Failure map

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: timm`, `yacs`, `mmcv`, `mmdet`, `mmseg`, `mmdet3d`, or `deepspeed` | The workflow-specific dependency stack is not installed. | Identify the sub-skill first. Install only the stack needed for that workflow, not every optional dependency in the repository. |
| OpenMMLab registry errors such as missing `InternImage` backbone | Custom modules were not imported or the command was run without the task directory on `PYTHONPATH`. | Use the sub-skill command builder; it prints commands with `PYTHONPATH` and working directory set for the selected task root. |
| `ModuleNotFoundError: DCNv3` | DCNv3 Python/CUDA extension is missing, built for another environment, or not on the task's import path. | Route to deployment. Confirm PyTorch CUDA wheel, `CUDA_HOME`, `nvcc`, compiler, and source/prebuilt wheel compatibility before building. |
| `NotImplementedError: Cuda is not availabel` during DCNv3 setup | The operator setup checks both `torch.cuda.is_available()` and `CUDA_HOME`; source contains the misspelled error text. A GPU driver alone does not satisfy source build requirements. | Install/use a compatible PyTorch CUDA wheel and CUDA toolkit with `nvcc`, or use a compatible prebuilt DCNv3 wheel. Do not call a CPU-only import a CUDA verification. |
| `ImportError`, `undefined symbol`, or segmentation fault from compiled packages | ABI mismatch among PyTorch, CUDA, `mmcv-full`, DCNv3, or mmdeploy custom ops. | Recreate the environment with aligned PyTorch/CUDA/mmcv/DCNv3 versions. Avoid mutating a working environment piecemeal unless the user approves. |
| NumPy or pydantic errors in old OpenMMLab configs | Newer NumPy/Pydantic/YAPF versions are incompatible with the old repo stack. | Use documented pins: `numpy<2`, `pydantic==1.10.13`, and `yapf==0.40.1` for detection where config formatting needs it. |
| Command builder works but model run fails | Helper only validated command shape; runtime dependencies, data, checkpoint, CUDA, and custom operators may still be missing. | Treat helper output as a plan. Run environment checks, verify data paths and checkpoint family, then execute intentionally. |
| Checkpoint load has many missing/unexpected keys | Checkpoint and config do not match task family/backbone/head or pretraining stage. | Re-pair config and checkpoint. Use classification weights only as pretrained backbones where the config expects them, not as full detector/segmentor checkpoints. |
| Dataset file-not-found or annotation mismatch | Data root/layout does not match the selected config family. | Read the sub-skill's data/config reference and override data roots with config options or a local config copy. Do not assume placeholder roots from examples are valid. |
| CUDA OOM | Model/backbone/resolution/batch too large; H/G/CB families are especially memory-heavy. | Reduce per-GPU batch size, enable checkpointing (`with_cp=True` when available), select a smaller backbone, reduce image size, or use more GPUs. |
| Distributed launch hangs | Port conflict, wrong GPU count, missing env variables, or mixed Slurm/torch launch strategy. | Regenerate command with explicit `--gpus` and `--port`. For Slurm, map scheduler variables to local policy rather than copying placeholders. |
| Hugging Face `trust_remote_code` prompt/error | Published InternImage Transformers models use custom code. | Use classification Hugging Face reference. Pass `trust_remote_code=True` only for trusted model IDs and ensure network/cache availability. |
| TensorRT/mmdeploy export cannot find `mmdeploy::TRTDCNv3` | InternImage DCNv3 TensorRT custom op has not been copied/built into mmdeploy's TensorRT backend. | Route to deployment; build/install mmdeploy with the bundled custom-op guidance before export. |
| OpenLane-V2 evaluation import fails with `cannot import name 'check_results'` | Inspected checkout has an empty preprocessing package initializer while the evaluation file imports `check_results` from it. | Use autonomous-driving validator for JSON schema checks. For full evaluation, patch/export `check_results` or patch the evaluation import, then rerun on a tiny or real validation fixture. |

## What the generated skill verified

Verified during creation:

- Repository evidence and sub-skill coverage were distilled into self-contained files.
- Generated Python helper scripts compile and expose help/dry-run behavior.
- A CPU OpenLane-V2 inspection environment imported the root package, direct schema checker, dataset/frame classes, IO utilities, and distance utility.
- The generated OpenLane-V2 JSON validator accepts a valid tiny fixture and rejects an invalid topology/ID fixture.

Not verified during creation:

- Full PyTorch model forward passes.
- DCNv3 compiled CUDA numerical parity tests.
- MMDetection/MMSegmentation/mmdet3d native train/eval/demo runs.
- Hugging Face downloads.
- TensorRT/mmdeploy export.
- Large dataset downloads or benchmark reproduction.

## When to stop and ask the user

Stop before executing if the next step would download large weights/data, install or downgrade broad dependency stacks, mutate a user environment, build CUDA/TensorRT extensions, launch multi-GPU/Slurm training, use credentials, or run benchmark-scale jobs. Present the exact command plan and required resources first.
