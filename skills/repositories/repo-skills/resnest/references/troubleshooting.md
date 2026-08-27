# ResNeSt Cross-Cutting Troubleshooting

Start here for failures that can affect more than one backend. Then use the nearest sub-skill troubleshooting reference for PyTorch, Gluon, or Detectron2-specific recovery.

## Fast diagnosis order

1. Run the root helper with no downloads:

   ```bash
   python scripts/check_resnest_install.py --model resnest50 --image-size 64
   ```

2. If the core PyTorch path fails, fix package requirements before debugging optional backends.
3. If optional Gluon or Detectron2 imports are missing, decide whether the user actually needs those workflows before installing heavyweight dependencies.
4. Use no-pretrained smoke checks before trying pretrained downloads, ImageNet, COCO, CUDA, Horovod, or full train/eval.

## Common failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: resnest` | Package is not installed in the active Python environment. | Install `resnest --pre` from PyPI or install the package from a trusted checkout, then rerun the root helper. |
| `ModuleNotFoundError: torch` | Core PyTorch runtime missing. | Install a PyTorch build compatible with the user's Python and CPU/CUDA backend before using `pytorch-models`. |
| `ModuleNotFoundError: fvcore` or `iopath` | Package support dependency missing; ResNeSt uses fvcore registries and iopath utilities. | Install package requirements, then rerun `python scripts/check_resnest_install.py`. |
| Root helper reports `resnest.gluon` missing because `mxnet` is missing | Gluon support is optional and MXNet was not installed. | If the task is PyTorch-only, ignore this optional skip. If Gluon is required, install a compatible MXNet wheel and read `gluon-models`. |
| Root helper reports `resnest.d2` missing because `detectron2` is missing | Detectron2 support is optional and not in the base package install. | If the task is classification-only, ignore this optional skip. If Detectron2 is required, install a Detectron2 build matching PyTorch/CUDA and read `detectron2-backbones`. |
| `pretrained=True` tries to download or fails offline | Official weights are not bundled with the package. | Retry with `pretrained=False`; only enable pretrained when network/cache access and checkpoint compatibility are confirmed. |
| Hash/checksum failure for weights or parameters | Partial/corrupt cache file or wrong mirror. | Delete the corrupted cached artifact and retry through a trusted channel, or stay with no-pretrained mode. |
| Classifier shape mismatch when loading pretrained classifier weights | ImageNet weights expect 1000 classes. | Keep the output classes at 1000 for pretrained load, then replace the classifier head for transfer learning; or use `pretrained=False`. |
| ImageNet validation cannot find data | Full validation needs a raw ImageNet layout or backend-specific RecordIO files. | Prepare the dataset outside this skill, verify train/val folders or RecordIO files, and only then run full validation. |
| COCO train/eval cannot find datasets | Detectron2 dataset names and annotation files are not registered/available. | Prepare COCO 2017 outside this skill, set the user's Detectron2 dataset root or custom registrations, and verify evaluator metadata. |
| CUDA or SyncBN errors | The workflow moved beyond CPU-safe inspection into GPU/distributed behavior. | Confirm GPU visibility, framework CUDA build, and distributed launcher. For config/debug work, prefer CPU/no-model probes or change norms only with an explicit behavior change. |
| `DropBlock2D` raises `NotImplementedError` in PyTorch | The PyTorch DropBlock class is a placeholder in this release. | Keep `dropblock_prob=0.0` unless the user supplies an implementation. |
| Detectron2 DCN operator errors | Deformable convolution ops are unavailable or incompatible. | Use a non-DCN config or install a matching Detectron2 build with working DCN operators. |
| User wants paper numbers from a tiny script | Tiny scripts only prove import/model tensor flow. | Explain that benchmark reproduction requires full data, exact preprocessing, pretrained weights, hardware, and backend-specific recipes. |

## Optional dependency policy

Do not install MXNet, GluonCV, Horovod, Detectron2, pycocotools, CUDA packages, or large dataset tooling unless the user's request specifically requires that optional workflow. The core ResNeSt package can be inspected and used through PyTorch without those optional stacks.

## Data and side-effect policy

Dataset preparation scripts for ImageNet and COCO are large and mutating: they check or extract archives, reorganize validation folders, download data, install COCO APIs, or create symlinks. Treat them as user-approved setup tasks, not routine verification. For ordinary skill use, document the required layout and run only safe import/config/tiny-tensor checks.

## When to route deeper

- PyTorch import/model/layer/training config errors: `sub-skills/pytorch-models/references/troubleshooting.md`.
- MXNet/Gluon/cache/RecordIO/Horovod errors: `sub-skills/gluon-models/references/troubleshooting.md`.
- Detectron2 config/backbone/SyncBN/DCN/COCO errors: `sub-skills/detectron2-backbones/references/troubleshooting.md`.
