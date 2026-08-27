# Classification Troubleshooting

Use this file for MambaVision package, classifier inference, pretrained checkpoint, validation, and benchmark problems. Route training-specific failures to `../training/SKILL.md`; route MMDetection or MMSegmentation failures to their sibling sub-skills.

## `mamba_ssm` build or import failures

Symptoms:

- `ModuleNotFoundError: No module named 'mamba_ssm'`
- `ImportError` from `mamba_ssm.ops.selective_scan_interface`
- Build logs mention `nvcc` missing, CUDA headers missing, build isolation, or a PyTorch/CUDA version mismatch.
- Runtime forward fails inside selective scan kernels.

Actions:

1. Confirm PyTorch and CUDA identity:

   ```bash
   python - <<'PY'
   import torch
   print('torch', torch.__version__)
   print('torch cuda', torch.version.cuda)
   print('cuda available', torch.cuda.is_available())
   if torch.cuda.is_available():
       print(torch.cuda.get_device_name(0))
   PY
   ```

2. Reinstall a CUDA-enabled PyTorch wheel that matches the host driver before installing `mamba-ssm`.
3. Prefer a prebuilt `mamba-ssm==2.2.4` wheel when available for the exact Python/PyTorch/CUDA combination.
4. If building from source, ensure `nvcc` and CUDA development headers are visible in the build environment. Avoid build isolation when it causes the build to see a different PyTorch version than the runtime environment.
5. Re-run a tiny no-download smoke after repair:

   ```bash
   python sub-skills/classification/scripts/smoke_mambavision_inference.py \
     --model mamba_vision_T --device cuda --height 64 --width 64 --batch-size 1
   ```

Do not count a CPU import as proof of the CUDA classification backend. The source dummy and throughput workflows are CUDA-oriented, and backend verification for meaningful MambaVision inference should include a CUDA forward pass when CUDA is claimed.

## `torch.cuda.is_available()` is false

Symptoms:

- The smoke helper exits with `CUDA was requested but torch.cuda.is_available() is False`.
- `model.cuda()` raises a CUDA initialization error.
- GPU is visible in system tools but PyTorch reports CPU-only.

Actions:

1. Check that the installed PyTorch build includes CUDA, not a CPU-only wheel.
2. Check `CUDA_VISIBLE_DEVICES`; an empty or invalid value hides GPUs from PyTorch.
3. Check driver compatibility with the wheel CUDA version.
4. In containers, ensure GPU runtime flags are enabled.
5. If no GPU is available, use `--device cpu` only for limited debugging. Expect slower execution and do not use it as a substitute for CUDA validation.

## Invalid model name

Symptoms:

- `KeyError` from `model_entrypoint(model_name)`.
- `Unknown model` or no registry match.

Use one of:

```text
mamba_vision_T
mamba_vision_T2
mamba_vision_S
mamba_vision_B
mamba_vision_B_21k
mamba_vision_L
mamba_vision_L_21k
mamba_vision_L2
mamba_vision_L2_512_21k
mamba_vision_L3_256_21k
mamba_vision_L3_512_21k
```

At runtime, inspect:

```python
from mambavision.models.registry import list_models
print(list_models('mamba_vision*'))
```

## Pretrained download/cache/model-path problems

Symptoms:

- `pretrained=True` tries to access the network unexpectedly.
- Download fails due to offline environment, proxy, TLS, or rate limits.
- Checkpoint file appears in an unintended temporary location.
- Validation of a custom checkpoint unexpectedly downloads a pretrained file first.

Actions:

1. For offline or no-download workflows, pass `pretrained=False` and omit `model_path`.
2. For local checkpoints, use `checkpoint_path`:

   ```python
   model = create_model(
       'mamba_vision_T',
       pretrained=False,
       checkpoint_path='./checkpoints/mambavision_tiny_1k.pth.tar',
   )
   ```

3. If intentionally using `pretrained=True`, pass an explicit writable `model_path`:

   ```python
   model = create_model(
       'mamba_vision_T',
       pretrained=True,
       model_path='./checkpoints/mambavision_tiny_1k.pth.tar',
   )
   ```

4. If the file exists but loading fails, confirm it belongs to the same factory family and resolution.
5. For `validate_pip_model`, remember that the entry point creates a pretrained package model internally and does not expose `model_path` as a CLI option. Use `validate.py --checkpoint ...` for offline custom-checkpoint validation.

## Checkpoint key or shape mismatch

Symptoms:

- Missing/unexpected keys during load.
- Classifier head size mismatch.
- First-layer shape mismatch after changing `in_chans`.
- Failures after changing architecture kwargs such as `dim`, `depths`, or `window_size`.

Actions:

- Use the exact factory matching the checkpoint family.
- Keep default architecture kwargs when loading released checkpoints.
- Keep `num_classes=1000` for released ImageNet-style checkpoints unless you intentionally discard or replace the head.
- Do not change `in_chans` when loading RGB pretrained checkpoints unless you implement first-layer adaptation.
- For a feature extractor with a custom head, first load the matching pretrained backbone defaults, then replace `model.head` in user code.

## Missing ImageNet/ImageFolder data

Symptoms:

- `FileNotFoundError` or `Found 0 images` from timm dataset creation.
- Accuracy is nonsensical because class folders or class-index mapping are wrong.
- `--results-file` fails because the parent directory does not exist.

Actions:

1. Check folder layout:

   ```text
   data_root/
     val/
       n01440764/*.JPEG
       n01443537/*.JPEG
       ...
   ```

2. Use:

   ```bash
   python <validation-entrypoint> \
     --model mamba_vision_T \
     --checkpoint ./checkpoints/mambavision_tiny_1k.pth.tar \
     --data-dir ./data_root \
     --split val \
     --batch-size 64 \
     --input-size 3 224 224 \
     --device cuda
   ```

3. If the validation directory itself contains class folders, pass that directory as `--data-dir`.
4. Create the results directory before using `--results-file`:

   ```bash
   mkdir -p ./results
   ```

5. Use a `--class-map` only when your class folder names do not already match the intended class index ordering.

## `--data_dir` is rejected

The parser defines `--data-dir` with a dash. If a copied command uses `--data_dir`, rewrite it:

```bash
# correct
--data-dir ./data/imagenet
```

## Input resolution or channels errors

Symptoms:

- Shape errors in patch embedding or first convolution.
- Checkpoint loading fails after changing channels.
- Very high-resolution inputs run out of memory.

Actions:

- Inputs must be `[B, C, H, W]`, not `[B, H, W, C]`.
- Use `C=3` for released RGB checkpoints.
- Arbitrary height/width is supported for inference, but memory and throughput scale with pixel count.
- Start with `mamba_vision_T`, batch size 1, and a small height/width when diagnosing.
- For real image accuracy, use model default preprocessing from `model.default_cfg` or the Hugging Face model config.

## Out of memory during validation or inference

Actions:

- Reduce `--batch-size` first.
- Use a smaller family (`T` before `S`, `B`, `L`, `L2`, `L3`).
- Use the published default resolution before experimenting with larger images.
- Try `--channels-last` and native AMP for throughput/validation if numerically acceptable.
- Use `--retry` with validation scripts so recognized OOM errors trigger batch-size decay.

## Throughput helper issues

Use `scripts/benchmark_mambavision.py`, not the original throughput workflow. The original workflow uses an undefined batch-size variable and assumes CUDA plus `ptflops`.

Common issues:

- CUDA requested but unavailable: install a CUDA-enabled PyTorch wheel or run only a non-comparable CPU debug timing.
- `ptflops` missing: omit `--flops`, or install `ptflops` and rerun with `--flops`.
- First run is slow: increase warmup and runs.
- Results differ from published table: record GPU model, PyTorch/CUDA versions, batch size, resolution, AMP dtype, channels-last setting, and whether FLOPs were measured.

Safe starting command:

```bash
python sub-skills/classification/scripts/benchmark_mambavision.py \
  --model mamba_vision_T \
  --device cuda \
  --resolution 224 \
  --batch-size 1 \
  --warmup 5 \
  --runs 20 \
  --amp \
  --channels-last
```

## Non-fatal timm warnings

`timm` may print warnings such as:

```text
FutureWarning: Importing from timm.models.registry is deprecated
FutureWarning: Importing from timm.models.layers is deprecated
```

These warnings are expected from the current MambaVision imports and are non-fatal. Continue if model construction and forward pass succeed. Treat them as actionable only if future `timm` versions remove the compatibility path and imports begin to fail.

## Do not troubleshoot downstream OpenMMLab here

If errors mention MMDetection, MMSegmentation, MMEngine, MMCV, COCO, ADE20K, Cascade Mask R-CNN, or UPerNet, switch to the object-detection or semantic-segmentation sub-skill. The base classification environment does not prove those optional stacks are installed.
