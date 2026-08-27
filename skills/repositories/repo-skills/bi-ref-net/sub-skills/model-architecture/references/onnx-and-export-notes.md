# ONNX and export notes

BiRefNet export is possible, but it is not a default-safe smoke task. The source tutorial treats ONNX conversion as a separate, backend-dependent workflow because the default architecture uses deformable convolution and large high-resolution tensors.

## What the official ONNX flow does

The distilled conversion flow is:

1. Select a `.pth` BiRefNet checkpoint and choose `device = 'cuda' if torch.cuda.is_available() else 'cpu'`.
2. Ensure the source `Config` backbone matches the checkpoint. For tiny/lite weights, use the current code key `swin_v1_t`; for standard large weights, use `swin_v1_l`.
3. Construct `BiRefNet(bb_pretrained=False)`.
4. Load the full checkpoint with `torch.load(..., weights_only=True)`, run `check_state_dict`, and call `load_state_dict`.
5. Move the model to the selected device and set `eval()`.
6. Register a custom/deform-conv ONNX exporter for `torchvision.ops.deform_conv2d`.
7. Export with a dummy input shaped like the intended inference size, commonly `(1, 3, 1024, 1024)`, using `torch.onnx.export(..., opset_version=17, input_names=['input_image'], output_names=['output_image'])`.
8. Load the ONNX file in ONNX Runtime with `CPUExecutionProvider` or `CUDAExecutionProvider`, run inference, apply sigmoid to the final output, and compare against PyTorch outputs.

## Deformable convolution caveat

The default decoder attention is `dec_att='ASPPDeformable'`. That path uses `torchvision.ops.deform_conv2d` through BiRefNet's deformable ASPP block. Plain `torch.onnx.export` may not know how to symbolize this operator. The source notebook used an external deform-conv exporter, patched helper logic for dynamic tensor dimension sizes, and registered the deform-conv ONNX op before export.

Operational implications:

- If export fails around `deform_conv2d`, `torchvision::deform_conv2d`, symbolic registration, or unknown custom ops, the issue is expected for the default architecture; use a tested deform-conv exporter or switch to an architecture/checkpoint that does not use deformable attention.
- If you alter `dec_att` to avoid deformable convolution, the checkpoint must have been trained with the same architecture. Do not silently change `dec_att` just to make an existing checkpoint export.
- Treat the exporter patch as version-sensitive; confirm it against the installed `torch`, `torchvision`, `onnx`, and `onnxscript` versions.

## Opset, provider, and package notes

- The source tutorial used `opset_version=17`.
- ONNX Runtime GPU is sensitive to the compatibility among `onnxruntime-gpu`, CUDA, and cuDNN. The source notes mention a working conversion context using `torch==2.0.1` with CUDA 11.8; that is a compatibility clue, not a universal requirement.
- Use `providers=['CPUExecutionProvider']` for CPU-only runs and `providers=['CUDAExecutionProvider']` for GPU runs. If CUDA provider is requested but unavailable, ONNX Runtime may fall back, error at session creation, or run far slower than expected.
- Optional packages are not part of the minimal BiRefNet import path. Conversion needs packages such as `onnx`, `onnxscript`, and `onnxruntime` or `onnxruntime-gpu` in addition to PyTorch/torchvision.

## Memory and runtime expectations

The source notebook records these practical warnings:

- Transforming a standard/default BiRefNet can need about `19.7GB` GPU memory.
- A small Colab-class runtime with around `12.7GB` RAM and `15GB` GPU memory was not enough for the default standard model conversion; the tutorial used a Swin-tiny/lite checkpoint as the example.
- At `1024x1024`, source notes reported ONNX inference slower than PyTorch for their tested setup: about `~165ms` on A100 for Swin-L and `~93.8ms` on A100 for Swin-T, roughly `~90%` and `~75%` more time respectively than the PyTorch path.
- PyTorch and converted ONNX predictions can differ slightly; small numerical differences are considered acceptable, but large or structured differences require checking preprocessing, sigmoid placement, output selection, opset/provider, and checkpoint/config matching.

## Export checklist before spending GPU time

1. Confirm the checkpoint family: standard large, lite/tiny, HR/2K, matting, portrait, COD, HRSOD, DIS, or custom.
2. Set the matching source architecture before constructing the model. At minimum confirm `config.bb`, `dec_att`, `dec_blk`, `dec_ipt`, `dec_ipt_split`, `mul_scl_ipt`, `cxt_num`, `squeeze_block`, `ms_supervision`, and `out_ref`.
3. Load the checkpoint with `bb_pretrained=False` and `check_state_dict`.
4. Run one PyTorch inference on a small representative image or synthetic tensor to confirm output indexing before export.
5. Check GPU memory headroom; use Swin-T/lite or a smaller resolution if the default Swin-L model does not fit.
6. Install and verify ONNX packages and the desired ONNX Runtime provider.
7. Register a deform-conv exporter if using the default `ASPPDeformable` decoder attention.
8. Export with fixed input shape unless dynamic axes have been explicitly tested for the chosen architecture and downstream runtime.
9. Compare PyTorch and ONNX outputs with identical preprocessing and `.sigmoid()` handling.

## What this sub-skill does not provide

- It does not bundle an ONNX conversion script because the source flow depends on optional packages, external deform-conv exporter code, large checkpoint files, and significant CPU/GPU memory.
- It does not claim TensorRT or third-party deployment correctness. The README mentions community TensorRT integrations, but those are separate projects with their own constraints.
- It does not make ONNX export part of the default verification gate. Treat export as an explicit, hardware-aware task.
