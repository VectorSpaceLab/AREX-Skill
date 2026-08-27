---
name: mri-operators
description: "Use fastMRI complex tensor math, centered FFT/IFFT, RSS coil
  combine, SSIM loss, crops, normalization, and metric shape checks safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI MRI Operators

Use this sub-skill when a task needs fastMRI tensor operators rather than data loading, model architecture design, or file-level leaderboard evaluation.

## Operator Checklist

- Use fastMRI's real/imaginary tensor convention: complex PyTorch tensors are real tensors whose final dimension has size `2`.
- Use `fastmri.fft2c(data, norm="ortho")` and `fastmri.ifft2c(data, norm="ortho")` for centered 2D transforms; spatial dimensions are `-3` and `-2`, and complex real/imag is `-1`.
- Use `fastmri.complex_abs`, `fastmri.complex_abs_sq`, `fastmri.complex_mul`, `fastmri.complex_conj`, and `fastmri.tensor_to_complex_np` for complex tensor math.
- Use `fastmri.rss(data, dim=...)` for real-valued coil images and `fastmri.rss_complex(data, dim=...)` for complex coil data; always set the coil dimension explicitly when it is not dimension `0`.
- Use `fastmri.data.transforms.center_crop`, `complex_center_crop`, `center_crop_to_smallest`, and `normalize_instance` for crop and normalization steps before losses or metrics.
- Use `fastmri.SSIMLoss` for tensor losses and `fastmri.evaluate` metrics for array-level reporting only after checking shape, crop, and finite-value assumptions.

## References

- [API reference](references/api-reference.md) explains exact operator signatures, tensor shape conventions, crop behavior, losses, metrics, and validation snippets.
- [Troubleshooting](references/troubleshooting.md) maps common FFT, complex dimension, RSS, crop, SSIM, metric, dtype/device, and dependency failures to fixes.
- [Smoke script](scripts/smoke_mri_ops.py) runs a tiny CPU-only check for complex absolute value, centered FFT/IFFT shape, RSS, and center crop; use it when validating an environment or debugging operator imports.

## Boundaries

- For reading k-space from fastMRI HDF5 files and applying masks in dataset transforms, use [data-loading](../data-loading/SKILL.md).
- For neural network architectures, training modules, VarNet, U-Net, and Lightning modules, use [model-architectures](../model-architectures/SKILL.md).
- For file-based reconstruction evaluation, saving submissions, and challenge output directories, use [evaluation-submission](../evaluation-submission/SKILL.md).
