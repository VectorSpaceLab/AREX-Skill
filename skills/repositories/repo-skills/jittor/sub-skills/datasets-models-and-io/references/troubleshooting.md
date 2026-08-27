# Datasets, transforms, models, and checkpoint troubleshooting

Use this matrix for data/model/I/O failures. It intentionally avoids source-checkout dependencies and networked tests.

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| MNIST/CIFAR constructor hangs or fails during a smoke test | `download=True` tried to reach the network. | Confirm the task allowed network and that the constructor was not created with default download behavior. | For smoke tests, replace with synthetic `TensorDataset`. For real data, pass an explicit prepared root and `download=False`, or run a separate approved download step. |
| `Dataset not found or corrupted` from CIFAR | Missing extracted files, failed integrity check, partial archive, or wrong `root`. | Verify the expected CIFAR extracted folder exists under the root and that train/test batch files are complete. | Delete or replace only the bad dataset copy, then re-download in an approved setup step, or point `root` at a known-good offline copy. Do not disable integrity checks silently. |
| MNIST file-open or gzip errors | One or more gzip files are missing or truncated. | Check that all four MNIST gzip files are present in the selected `data_root`. | Re-stage the files from a verified source, or let `download=True` run only when network use is permitted. |
| VOC fails at construction with missing file assertions | The VOC directory tree is incomplete or split name is wrong. | Check `ImageSets/Segmentation/<split>.txt`, `JPEGImages`, and `SegmentationClass`. | Prepare the VOC tree explicitly; Jittor's `VOC` constructor does not provide an automatic download path. |
| Jittor import on a CUDA-visible host fails with a gcc/nvcc mismatch | CUDA auto-detection found an unusable `nvcc` before the CPU smoke finished importing. | Check whether the task needs CUDA at all and whether the smoke only needs CPU behavior. | For a CPU-only smoke, clear `nvcc_path` before import or use the bundled smoke script, which does so internally. |
| Pretrained model constructor touches the network | `pretrained=True` calls `model.load("jittorhub://...")`. | Search the constructor call for `pretrained=True`. | Use `pretrained=False` for API/shape checks. If pretrained weights are required offline, load a verified local checkpoint explicitly. |
| Pretrained or Jittor checkpoint reports checksum/corruption errors | Interrupted download or stale local checkpoint file. | Try `pretrained=False` to isolate constructor correctness; then validate the checkpoint file independently. | Replace the bad checkpoint in a controlled setup step or point `model.load` to a verified local file. |
| ImageFolder finds zero or wrong labels | Directory is flat, class directories are misnamed, files use unsupported extensions, or labels rely on unsorted order. | Ensure images live under `root/class_name/...`; inspect sorted class names and `class_to_idx`. | Reorganize data into class subdirectories or use a custom `Dataset` when labels are not folder-derived. |
| ImageFolder output has shape `[B,H,W,3]` instead of `[B,3,H,W]` | Raw PIL images were collated without a CHW transform. | Print one batch shape before model input. | Add a transform that converts PIL to CHW, such as `ToTensor()` plus `ImageNormalize()`, or `ImageNormalize()` on RGB PIL after PIL-only augmentations. |
| Model forward fails with channel or shape mismatch | Input is HWC, missing batch dimension, grayscale, or not three-channel NCHW. | Check `list(x.shape)` immediately before the model. | Convert image data to `[N,3,H,W]`. For grayscale data, replicate/convert to RGB if using ImageNet-style models. |
| `ToPILImage` gives wrong colors or shape errors | Input was CHW but `ToPILImage` expects HWC for NumPy/Var. | Check whether data is `[C,H,W]` or `[H,W,C]`. | Transpose CHW to HWC before `ToPILImage`; keep PIL-only transforms before `ToTensor`. |
| `ToTensor` did not convert HWC NumPy to CHW | Jittor preserves 3D NumPy axis order in `to_tensor`. | Confirm whether the input to `ToTensor` was PIL or NumPy. | For HWC NumPy, transpose manually or convert to PIL first. For PIL, `ToTensor` returns CHW. |
| `ImageNormalize` broadcasting error or wrong normalization | HWC array passed where CHW/NCHW was expected. | Inspect the last three dimensions and channel axis. | Use `ToTensor` on PIL first, or transpose arrays to CHW before normalization. |
| Transform chain unexpectedly calls PIL conversion after `ToTensor` | PIL-only transform placed after array conversion. | Review `Compose` order. | Put `Resize`, crops, flips, perspective, and color jitter before `ToTensor`/`ImageNormalize`. |
| Data workers hang or fail silently | Multiprocessing worker exception, non-picklable dataset state, CUDA/Jittor state inside workers, or too many workers for the host. | Re-run with `num_workers=0`; if needed, set `DISABLE_MULTIPROCESSING=1` for diagnosis. | Keep `__getitem__` simple and CPU/local-file based; avoid long loops and GPU state in workers; increase workers only after single-process iteration is correct. |
| Worker results differ unexpectedly | Random seeds or stochastic transforms differ per worker. | Fix Python/NumPy/Jittor seeds and compare `num_workers=0` with a small worker count. | Use deterministic transforms for tests; reserve stochastic augmentation for training runs. |
| `state_dict(to="torch")` or PyTorch converter helper fails to import | Optional PyTorch dependency is not installed. | Try `import torch` only if interop is required. | Use native Jittor `.pkl` checkpoints when possible. Install PyTorch only for explicit interop tasks. |
| `model.load` completes but outputs are wrong | Key mismatch, shape mismatch, architecture mismatch, train/eval mode mismatch, or silently skipped parameters. | Compare state-dict keys and shapes before loading; inspect Jittor warnings. | Use matching constructors and `num_classes`; run `eval()` for inference checks; compare a small known input after load. |
| PyTorch `.pth` load fails with pickle/custom-class errors | Checkpoint stores full Python objects, custom classes, optimizer internals, or unsupported storages. | Determine whether the file is a plain tensor state dict. | Export a plain state dict from the source framework when possible. Otherwise treat the checkpoint as unsupported by Jittor's helper. |

## Offline triage for CIFAR/MNIST failures

1. Reproduce with `download=False` and the same root. If it fails immediately, the local files or layout are missing/corrupt.
2. Reproduce in a separate approved setup step with `download=True`. If that fails before integrity checks, it is a network or mirror issue.
3. If download succeeds but the constructor still reports corruption, treat it as an integrity/cache problem and replace the staged data copy.
4. For unrelated model/data smoke, stop using the built-in dataset and switch to synthetic `TensorDataset`.

## Offline triage for model weights

1. Re-run the constructor with `pretrained=False`. If shape smoke passes, the architecture is fine.
2. If `pretrained=True` is required, check whether network use is allowed and whether the checkpoint was already staged.
3. If a local checkpoint is used, compare keys and shapes before `load_parameters`.
4. Always perform a small forward pass after load; loading warnings can be non-fatal but still indicate an unusable state.
