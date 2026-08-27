# MMCV Ops Reference

`mmcv.ops` is the compiled-ops surface for detection, segmentation, 3D perception, sparse tensors, attention kernels, and specialized losses. In MMCV 2.x, importing this module requires the full `mmcv` package and a working `mmcv._ext` extension. The `mmcv-lite` package imports as `mmcv` but does not provide compiled ops.

## Functional Families

| Family | Representative APIs | Typical use | Full `mmcv` required? |
| --- | --- | --- | --- |
| ROI and pooling | `RoIAlign`, `roi_align`, `RoIAlignRotated`, `roi_align_rotated`, `RiRoIAlignRotated`, `RoIPool`, `DeformRoIPool`, `PrRoIPool`, `RoIAwarePool3d`, `RoIPointPool3d`, `BezierAlign`, `BorderAlign` | Detection/instance segmentation pooling, rotated boxes, 3D ROI pooling | Yes |
| NMS | `nms`, `soft_nms`, `batched_nms`, `nms_match`, `nms_rotated`, `nms_quadri`, `nms3d`, `nms3d_normal`, `nms_bev`, `nms_normal_bev` | Post-processing boxes and 3D boxes | Yes |
| IoU and boxes | `box_iou_rotated`, `box_iou_quadri`, `bbox_overlaps`, `boxes_iou3d`, `boxes_iou_bev`, `boxes_overlap_bev`, `convex_iou`, `convex_giou`, `diff_iou_rotated_2d`, `diff_iou_rotated_3d`, `min_area_polygons` | Rotated/quadrilateral/3D box geometry | Yes |
| Deformable conv and pool | `DeformConv2d`, `deform_conv2d`, `DeformConv2dPack`, `ModulatedDeformConv2d`, `modulated_deform_conv2d`, `ModulatedDeformRoIPoolPack` | Deformable convolution layers and pooling | Yes |
| Point cloud and 3D | `ball_query`, `knn`, `furthest_point_sample`, `furthest_point_sample_with_dist`, `gather_points`, `grouping_operation`, `three_nn`, `three_interpolate`, `points_in_boxes_*`, `points_in_polygons`, `Voxelization`, `voxelization`, `DynamicScatter`, `RoIAwarePool3d`, `RoIPointPool3d` | PointNet-style grouping, 3D boxes, voxelization | Yes |
| Sparse convolution | `SparseConvTensor`, `SparseConv2d`, `SparseConv3d`, `SubMConv2d`, `SubMConv3d`, `SparseInverseConv*`, `SparseConvTranspose*`, `SparseMaxPool*`, `SparseSequential`, `SparseModule` | Sparse 2D/3D convolution workflows | Yes |
| Attention and context | `MultiScaleDeformableAttention`, `CrissCrossAttention`, `cc_attention` | Transformer/dense context kernels | Yes |
| Losses | `SigmoidFocalLoss`, `sigmoid_focal_loss`, `SoftmaxFocalLoss`, `softmax_focal_loss` | Detection losses implemented with native kernels | Yes |
| Image and kernel ops | `CARAFE`, `carafe`, `CornerPool`, `MaskedConv2d`, `PSAMask`, `SAConv2d`, `TINShift`, `active_rotated_filter`, `rotated_feature_align`, `pixel_group`, `contour_expand`, `upfirdn2d`, `filter2d`, `upsample2d`, `fused_bias_leakyrelu`, `bias_act`, `filtered_lrelu`, `conv2d`, `conv_transpose2d`, `Conv2d`, `ConvTranspose2d`, `Linear`, `MaxPool2d`, `SyncBatchNorm` | Specialized kernels used by detection, segmentation, GAN, and model layers | Usually yes; some wrappers call PyTorch but import through `mmcv.ops` still requires the package surface. |

## Backend Support Cautions

The docs list support by op across CPU, CUDA, MLU, MPS, and Ascend. Treat backend support as per-op, not package-wide:

| Backend | Coverage pattern |
| --- | --- |
| CPU | Selected geometry, ROI, deformable convolution, voxelization, contour/pixel grouping, and some pooling/alignment kernels. |
| CUDA | Broadest coverage, including most detection, 3D, sparse, attention, and loss kernels; still depends on wheel/build flags. |
| MLU | Partial coverage for several detection, ROI, 3D, attention, loss, and voxelization kernels when built with Torch-MLU. |
| MUSA | Source has MUSA paths for selected kernels; require the matching Torch-MUSA stack and build path. |
| NPU/Ascend | Partial coverage for selected detection, ROI, point, loss, and image kernels when built with `torch_npu`. |
| MPS | Very narrow documented support; do not assume an op works on MPS just because PyTorch MPS is available. |
| ROCm/HIP or DIOPI/DIPU | Build paths exist, but compatibility is stack-specific and should be validated with targeted smoke checks. |

- CPU support exists for selected ops such as NMS, rotated/quadri IoU, ROIAlign, deformable convolution, voxelization, contour/pixel grouping, and some pooling/alignment kernels.
- CUDA has the broadest coverage, but a full `mmcv` install can still lack a CUDA implementation if it was built CPU-only.
- MLU, MUSA, NPU/Ascend, MPS, ROCm/HIP, and DIOPI/DIPU paths require matching PyTorch backend packages and build flags; support is narrower than CUDA and varies by op.
- A successful `import mmcv.ops` only proves that the extension loaded; it does not guarantee that a specific op supports a specific device.
- Device-specific runtime errors such as `nms is not compiled with GPU support`, `invalid device function`, and `no kernel image is available for execution` usually indicate backend/build mismatch rather than Python API misuse.

## Representative Availability Probes

Check only import availability:

```bash
python -c "import mmcv, mmcv.ops; print(mmcv.__version__)"
```

Check compiler metadata, which requires `mmcv.ops.info` and `mmcv._ext`:

```bash
python -c "from mmcv.ops import get_compiler_version, get_compiling_cuda_version; print(get_compiler_version()); print(get_compiling_cuda_version())"
```

Run this skill's bundled smoke checker for a graceful report:

```bash
python scripts/check_mmcv_install.py --require-ops
```

## When Full MMCV Is Required

Choose full `mmcv` whenever user code imports from `mmcv.ops`, even if the target op is CPU-capable. The lite package intentionally omits `mmcv._ext`; in a lite environment, calls such as `from mmcv.ops import nms` or `from mmcv.ops import box_iou_rotated` fail before reaching any device-specific branch.

If a downstream OpenMMLab project only uses image I/O, transforms, visualization, or utilities, `mmcv-lite` can be sufficient. If it imports detectors, heads, assigners, post-processing, deformable layers, rotated-box geometry, sparse tensors, or 3D modules that call `mmcv.ops`, use full `mmcv`.
