# Feature and matching API reference

## Classical responses and detectors

Use response functions when you need low-level score maps: `harris_response`, `gftt_response`, `hessian_response`, `dog_response`, and `dog_response_single`. Detector modules such as `CornerHarris`, `CornerGFTT`, `BlobHessian`, `BlobDoG`, `ScaleSpaceDetector`, `MultiResolutionDetector`, and `KeyNetDetector` build keypoint selection on top of response maps and pyramids.

## Descriptors and local feature wrappers

| API | Use |
| --- | --- |
| `SIFTDescriptor`, `DenseSIFTDescriptor`, `SIFTFeature`, `SIFTFeatureScaleSpace` | SIFT-like descriptor and local-feature workflows without relying on external OpenCV calls. |
| `HardNet`, `HardNet8`, `HyNet`, `TFeat`, `SOSNet`, `MKDDescriptor` | Descriptor networks or descriptor modules. Check pretrained/cache behavior before requesting weights. |
| `LAFDescriptor`, `get_laf_descriptors` | Extract descriptors from image patches defined by LAFs. |
| `LocalFeature`, `LocalFeatureMatcher` | Combine detector/descriptor/matcher modules into a higher-level pipeline. |

## LAF utilities

Useful local-affine-frame helpers include `laf_from_center_scale_ori`, `get_laf_center`, `get_laf_scale`, `get_laf_orientation`, `scale_laf`, `rotate_laf`, `normalize_laf`, `denormalize_laf`, `laf_to_boundary_points`, `laf_to_three_points`, `laf_from_three_points`, `laf_is_inside_image`, `make_upright`, and `perspective_transform_lafs`.

LAF tensors encode a local affine frame rather than just a keypoint coordinate. Before passing LAFs to a matcher or descriptor, assert their batch and frame dimensions match the image batch.

## Descriptor matching

Representative function signatures:

```python
match_nn(desc1, desc2, dm=None)
match_mnn(desc1, desc2, dm=None)
match_snn(desc1, desc2, th=0.8, dm=None)
match_smnn(desc1, desc2, th=0.95, dm=None)
```

Module forms include `DescriptorMatcher`, `GeometryAwareDescriptorMatcher`, `LocalFeatureMatcher`, `LightGlueMatcher`, and steered matcher variants.

## Learned features and matchers

| API | Notes |
| --- | --- |
| `DISK`, `DeDoDe`, `ALIKED`, `XFeat` | Learned local-feature models. Some constructors can download or require cached weights; keep that explicit. |
| `LoFTR` | Detector-free matching. `pretrained="outdoor"` or `"indoor"` is optional and may download/cache weights. Inputs are image dictionaries such as `{"image0": ..., "image1": ...}`. |
| `LightGlue`, `LightGlueMatcher`, `OnnxLightGlue` | Learned matcher family. ONNX usage may require optional ONNX Runtime dependencies. |
| `SOLD2` | Line/feature model with optional weight handling. |

Do not make a pretrained model the default validation path unless the user already authorized network/cache use or supplied weights.
