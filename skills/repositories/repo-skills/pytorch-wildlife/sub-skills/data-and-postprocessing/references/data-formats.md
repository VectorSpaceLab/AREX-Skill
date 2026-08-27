# Data and preprocessing contracts

## Image-folder datasets

Import `ClassificationImageFolder`, `DetectionImageFolder`, and
`DetectionCrops` from `PytorchWildlife.data.datasets`. The folder datasets
recursively walk the supplied directory and accept filenames ending in
`.jpg`, `.jpeg`, `.png`, `.ppm`, `.bmp`, `.pgm`, `.tif`, `.tiff`, or `.webp`
(case-insensitive). They do not enforce class subdirectories or sort the
recursive walk; if stable ordering matters, sort the resulting paths before
building a custom loader.

Both folder loaders open each image and convert it to RGB before applying the
optional callable transform. `ClassificationImageFolder[i]` returns:

```text
(transformed_image, img_path)
```

`DetectionImageFolder[i]` returns:

```text
(transformed_image, img_path, torch.tensor((original_height, original_width)))
```

The path is the discovered filesystem path, and the size is captured before
transformation. A transform can therefore resize or normalize the image
without losing the source dimensions needed to reverse detection coordinates.
Pillow's truncated-image loading compatibility is enabled by the package;
invalid or unreadable files can still fail during item access.

## DetectionCrops

`DetectionCrops(detection_results, transform=None, path_head=None,
animal_cls_id=0)` consumes the list returned by batch detection. Each result
must expose `img_id` and a `supervision.Detections` object at `detections`.
For every detection whose `class_id` equals `animal_cls_id` (default `0`), it
records the image id and `xyxy` box. An item resolves the image as
`path_head / img_id` when `path_head` is provided, otherwise it treats
`img_id` as the path; it converts to RGB, crops the box with
`supervision.crop_image`, applies the optional transform, and returns
`(crop, img_path)`.

This is a crop dataset, not a detector. It assumes boxes are valid image-space
`[x1, y1, x2, y2]` coordinates and assumes the detector's image ids can be
resolved from `path_head`. It does not carry the detector index in its output;
keep the dataset order aligned with classifier batch output and use the image
id to group results.

## Input choices

- Use `DetectionImageFolder` with `MegaDetector_v5_Transform` for the
  detector batch-loader path.
- Use `ClassificationImageFolder` with
  `Classification_Inference_Transform` for direct classifier images.
- Use `DetectionCrops` with the classification transform for detector-to-
  classifier chaining. The model's own batch classification contract should
  receive a loader that yields the crop tensor and path.
- Keep original paths outside serialized public JSON when they reveal local
  machine layout. Use `exclude_file_path` in the serializers or generate
  relative ids before handing results to downstream users.

## Transform selection

`MegaDetector_v5_Transform(target_size=1280, stride=32)` letterboxes to the
requested square target while retaining aspect ratio. `letterbox` accepts a
PIL image or CHW tensor and returns a float tensor in `[C,H,W]`; it scales to
`[0,1]`, pads with value `114/255`, and by default uses `auto=False`,
`scaleFill=False`, `scaleup=True`. Set `scaleup=False` to avoid enlarging
small images. The stride is used when `auto=True`; the default fixed target
keeps the requested dimensions.

`Classification_Inference_Transform(target_size=224, **kwargs)` resizes to
`(target_size, target_size)`, converts to a tensor, and normalizes channels
with ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation
`(0.229, 0.224, 0.225)`. Extra keyword arguments are passed to torchvision's
`Resize`; use a PIL RGB input. This transform intentionally resizes without
preserving aspect ratio.
