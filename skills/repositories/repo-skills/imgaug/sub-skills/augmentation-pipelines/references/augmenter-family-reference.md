# Augmenter family reference

Read this when selecting an imgaug augmenter family for a task.

## Composition and control

| Need | Typical classes/functions |
| --- | --- |
| Ordered list | `Sequential` |
| Apply a random subset | `SomeOf` |
| Pick exactly one child | `OneOf` |
| Probability-gated branch | `Sometimes` |
| Channel-specific augmentation | `WithChannels` |
| Custom callback | `Lambda` |
| Input shape guard | `AssertShape` |
| Remove or clip coordinate-based augmentables | `RemoveCBAsByOutOfImageFraction`, `ClipCBAsToImagePlanes` |

## Size and geometry

Use these for spatial changes. When annotations must stay aligned, pass images and augmentables in one call or make the pipeline deterministic.

- `Affine`, `ScaleX`, `ScaleY`, `TranslateX`, `TranslateY`, `Rotate`, `ShearX`, `ShearY`
- `AffineCv2`, `PiecewiseAffine`, `PerspectiveTransform`, `ElasticTransformation`, `Rot90`, `Jigsaw`
- `Resize`, `CropAndPad`, `Pad`, `Crop`, fixed-size/aspect-ratio/multiple/power helpers

Important defaults and knobs:

- `Affine(..., fit_output=False, backend='auto')` keeps the original frame unless `fit_output` is changed.
- `CropAndPad(..., keep_size=True)` resizes back by default.
- Dense segmentation maps should use nearest-neighbor semantics; heatmaps are continuous.

## Pixel intensity, noise, compression, and dropout

- Add/multiply: `Add`, `AddElementwise`, `Multiply`, `MultiplyElementwise`
- Noise: `AdditiveGaussianNoise`, `AdditiveLaplaceNoise`, `AdditivePoissonNoise`, `SaltAndPepper`, `ImpulseNoise`
- Dropout: `Dropout`, `CoarseDropout`, `Dropout2d`, `TotalDropout`, `Cutout`
- Inversion/compression: `Invert`, `Solarize`, `JpegCompression`

Use `per_channel=True` or a probability such as `per_channel=0.5` when channel-wise sampling is intended.

## Blur, convolution, contrast, and edges

- Blur: `GaussianBlur`, `AverageBlur`, `MedianBlur`, `BilateralBlur`, `MotionBlur`, `MeanShiftBlur`
- Convolution-like: `Convolve`, `Sharpen`, `Emboss`, `EdgeDetect`, `DirectedEdgeDetect`
- Contrast: `GammaContrast`, `SigmoidContrast`, `LogContrast`, `LinearContrast`, `CLAHE`, `HistogramEqualization`
- Edge detector: `Canny`

## Color and PIL-like transforms

- Color spaces/channels: `InColorspace`, `WithColorspace`, `WithBrightnessChannels`, `WithHueAndSaturation`, `ChangeColorspace`
- Hue/saturation/brightness: `MultiplyHue`, `MultiplySaturation`, `AddToHue`, `AddToSaturation`, `MultiplyBrightness`, `AddToBrightness`
- Quantization and style: `KMeansColorQuantization`, `UniformColorQuantization`, `Posterize`, `Grayscale`, `ChangeColorTemperature`, `Cartoon`
- PIL-like module: `iaa.pillike` contains `Solarize`, `Posterize`, `Equalize`, `Autocontrast`, enhancement and filter wrappers.

Color tasks should explicitly state RGB/BGR expectations. OpenCV loaders return BGR by default.

## Blending, segmentation-like effects, weather, and collections

- Blending: `BlendAlpha`, `BlendAlphaElementwise`, `BlendAlphaSimplexNoise`, `BlendAlphaFrequencyNoise`, `BlendAlphaSomeColors`, `BlendAlphaSegMapClassIds`, `BlendAlphaBoundingBoxes`
- Segmentation effects: `Superpixels`, `Voronoi`, `UniformVoronoi`, `RegularGridVoronoi`, point samplers
- Weather: `FastSnowyLandscape`, `Clouds`, `Fog`, `Snowflakes`, `Rain`
- Collection recipes: `RandAugment`
- Optional corruptions: `iaa.imgcorruptlike` mirrors image-corruption effects when its optional dependency is installed.

## Safe contact sheet

Use `scripts/generate_augmentation_contact_sheet.py` to render a tiny headless contact sheet from a built-in sample image. The script writes an output image only when requested and avoids GUI display.
