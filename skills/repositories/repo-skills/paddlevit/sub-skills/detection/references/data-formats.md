# Detection data formats

## COCO root

Pass the dataset **root** with `-data_path`, for example `<coco-root>`, not
`<coco-root>/train2017` or `<coco-root>/val2017`. The source resolves:

```text
<data_path>/annotations/instances_train2017.json
<data_path>/annotations/instances_val2017.json
<data_path>/train2017/<file_name>
<data_path>/val2017/<file_name>
```

Other annotation JSON files may coexist, but detection requires the two
`instances_*2017.json` files. Images are loaded as RGB with Pillow. The
`images[].file_name` value is joined to the selected split directory, so an
absolute or traversal-like filename should be rejected during validation.

## Annotation JSON

The minimum useful COCO detection document has `images`, `annotations`, and
`categories` arrays:

```json
{
  "images": [{"id": 1, "file_name": "000000000001.jpg", "width": 32, "height": 24}],
  "annotations": [{
    "id": 1, "image_id": 1, "category_id": 1,
    "bbox": [4, 3, 10, 8], "area": 80, "iscrowd": 0
  }],
  "categories": [{"id": 1, "name": "object"}]
}
```

`bbox` is `[x, y, width, height]` with the origin at the top-left. `width`
and `height` must be positive after clipping/validation. `image_id` must point
to an image and `category_id` must point to a declared category. Annotation
IDs should be unique. `area` is required by the source target preparation;
`iscrowd` defaults to zero in the repository code but should be explicit in
new fixtures. Segmentation is optional for bbox detection and is only decoded
when `return_masks=True`; this route does not own segmentation workflows.

Use `check_coco_layout.py` to validate these invariants and image existence.
Its default mode does not require `pycocotools`; `--check-api` additionally
loads the JSON through the COCO API, and `--check-images` uses Pillow to decode
referenced files and compare their dimensions with `images[].width/height`.

## Target representation after preparation

All families initially convert COCO boxes to absolute corner coordinates:
`[x0, y0, x1, y1]`, discard crowd annotations, and remove non-positive boxes.
The family transforms then update boxes for crop/flip/resize and normalize the
image with ImageNet mean/std.

DETR's final target fields include:

```text
labels       [N] category labels
boxes        [N,4] normalized [cx,cy,w,h]
image_id     original COCO image ID
orig_size    [height,width]
size         transformed [height,width]
area         [N]
iscrowd      [N]
```

Swin/PVTv2 convert to the RPN/RoI form:

```text
gt_boxes       [N,4] absolute [x0,y0,x1,y1]
gt_classes     [N] contiguous class indices
image_id       original COCO image ID
imgs_shape     [height,width] after transform
scale_factor_wh [width_scale,height_scale] from original to transformed image
area, iscrowd, orig_size as available
```

Swin/PVTv2 map sparse COCO category IDs to contiguous indices through
`cats2ids`. DETR's target path does not use that same adapter; do not copy a
class mapping between families without checking the local code.

## Batch and output formats

DETR collates variable-size tensors into a nested padded tensor with a spatial
mask. Swin/PVTv2 collate pads to size divisibility 32 and batches scalar fields
while retaining per-image lists for variable-length boxes. A valid detection
fixture must include at least one non-empty target; the Swin/PVTv2 collate
filters empty `gt_boxes` and has a refill path that is unsuitable for an
all-empty batch.

DETR model outputs:

```text
pred_logits [B, Q, C+1]
pred_boxes  [B, Q, 4] normalized center-size
```

DETR postprocess outputs one dict per image with `scores`, `labels`, and
absolute `boxes [Q,4]`.

Swin/PVTv2 evaluation output rows use:

```text
[label, confidence, xmin, ymin, xmax, ymax]
```

with a companion count per batch image. COCO adapter dictionaries use
`boxes`, `scores`, and `labels`, keyed by the original `image_id`.
