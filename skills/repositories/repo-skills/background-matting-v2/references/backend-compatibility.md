# Backend Compatibility

## Purpose

Use this when choosing between PyTorch, TorchScript, and ONNX or when deciding
whether a workflow is CPU-friendly or CUDA-gated.

## Summary

| Workflow | Backend stance | Notes |
| --- | --- | --- |
| `MattingBase` / `MattingRefine` research inference | PyTorch | Main source-model path.
| TorchScript export / runtime | Production-oriented | `MattingRefine` hoists refine attributes so they can be changed after loading.
| ONNX export / runtime | Experimental | Export works with compatibility knobs for patch crop/replace behavior and needs the `onnx` exporter package plus ONNX Runtime for the smoke helper.
| Image / video demo CLIs | PyTorch | Can run on CPU or CUDA, but CUDA is the normal high-resolution path.
| Webcam demo | CUDA-oriented | Needs local camera, a GUI display, and fast GPU inference to be practical.
| Training | CUDA-required in practice | `train_refine.py` uses DDP/NCCL and expects multiple GPUs when available.

## Important compatibility facts

- `MattingRefine` accepts patch crop methods `unfold`, `roi_align`, and
  `gather`.
- `MattingRefine` accepts patch replace methods `scatter_nd` and
  `scatter_element`.
- The ONNX export CLI exposes those methods because backend support varies by
  runtime.
- `backbone_scale` must stay at or below `0.5`.
- `MattingRefine` requires input height and width divisible by 4.
- The README recommends `backbone_scale=0.25, refine_sample_pixels=80000` for
  HD and `backbone_scale=0.125, refine_sample_pixels=320000` for 4K.

## Practical selection guidance

- Choose PyTorch when you want to inspect or use the source model directly.
- Choose TorchScript when you need a self-contained scripted module with the
  same model behavior.
- Choose ONNX when you need export compatibility or interop with ONNX Runtime
  and accept slower or less certain backend behavior.
