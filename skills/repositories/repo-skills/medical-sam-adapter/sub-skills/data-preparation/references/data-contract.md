# Sample and prompt contract

This contract is for one dataset item before `DataLoader` adds a batch axis. The
core loops consume `[B,C,H,W]` for 2D and `[B,C,H,W,D]` for 3D. Do not validate a
single item as if its first dimension were `B`.

## Required fields

| Field | Required by the documented custom contract | Accepted form and source meaning |
|---|---|---|
| `image` | yes | Numeric array/tensor shaped `[C,H,W]` for 2D or `[C,H,W,D]` for 3D. Every dimension is positive. Built-in 2D image adapters normally emit `C=3`; direct 3D adapters emit `C=1`. |
| `label` | yes | Numeric mask/label with the same rank as `image`. Its H/W axes correspond to the image's H/W axes; the source may resize them separately to `image_size` and `out_size`, but it must not lose spatial alignment. For 3D, depth `D` must match exactly. |
| `p_label` | yes | Prompt label `1` for positive and `0` for background/negative. A scalar broadcasts to one prompt; a vector must align with multiple 2D prompts or depth prompts. |
| `pt` | yes for the prompt-based loops | 2D one point `[x,y]` or multiple points `[N,2]`; 3D one point per slice, conventionally `[2,D]` (or batched `[B,2,D]` after collation). The documented custom convention is x/width first, y/height second. |
| `image_meta_dict` | optional in the README, operationally needed by the current core loop | Mapping with stable `filename_or_obj` naming. The source training/evaluation loop reads this field when constructing visualization names, so include it for an unmodified run. Do not store a machine-specific absolute path as the name. |

The validator accepts shape declarations rather than decoding image files. A
minimal JSON declaration is:

```json
{
  "dataset": "isic",
  "image_shape": [3, 256, 256],
  "label_shape": [1, 256, 256],
  "p_label": 1,
  "pt": [128, 64],
  "image_meta_dict": {"filename_or_obj": "case-001"}
}
```

Equivalent field objects are `"image": {"shape": [3,256,256]}` and
`"label": {"shape": [1,256,256]}`. Small nested numeric arrays can be used
instead. NPZ input may contain `image` and `label` arrays or `image_shape` and
`label_shape` declarations, plus `p_label` and `pt`. The validator opens NPZ
with `allow_pickle=False` and never writes an output archive.

## Shape, channel, and depth rules

- Reject `[H,W,C]`, flattened arrays, and a single item declared as
  `[B,C,H,W]` or `[B,C,H,W,D]`. The batch dimension is added later.
- The image and label must have the same rank and positive spatial axes. H/W
  may differ numerically when the source's `image_size` and `out_size` differ;
  in that case both still refer to the same case and field of view. Use the
  validator's strict spatial option when a custom adapter requires exact H/W.
- A 3D label must have the same depth as its image. `chunk` is a crop/window
  depth and is not an extra axis. MONAI transformations can change post-load
  H/W/D, so raw NIfTI header dimensions alone are not enough.
- Built-in 2D image adapters are RGB `[3,H,W]`, including LIDC's class after
  its explicit repeat. A grayscale custom class must make its model input
  expectation explicit; the repository does not automatically repeat arbitrary
  custom images.
- Direct 3D adapters return `[1,H,W,D]` image and mask. The training/evaluation
  loop turns slices into `[B*D,C,H,W]` and repeats each image slice to three
  channels before passing it to SAM.

## Mask and multimask conventions

A binary target uses background/foreground values. A class-map target may hold
integer class ids before an adapter selects or binarizes them. Do not convert a
multi-class label map into independent prompt channels without deciding how the
selected model consumes it.

- **REFUGE:** the adapter averages seven cup raters into channel 0 and seven
  disc raters into channel 1, then concatenates `[cup, disc]`. Missing raters
  must be fixed in the layout; do not silently average a subset.
- **LIDC:** the class averages its multi-rater masks, but the registered `LIDC`
  dispatcher calls undefined `MyLIDC`; this is a source blocker, not a mask
  contract that can be cleared by metadata alone.
- **`-multimask_output`:** an integer decoder/class-output request. The original
  SAM branch requests multiple masks for values greater than one. EfficientSAM
  and MobileSAM force `multimask_output=False` in the source loop. The flag
  cannot create an absent cup/disc rater or repair a wrong label channel count.
- Optional `box` values appear in some legacy adapters, but the core training
  and validation calls pass `boxes=None`. Treat boxes as adapter-specific until
  a separate consumer is verified.
- `multi_rater` may be retained as extra LIDC metadata; it does not replace
  `label`.

## Prompt rules

For a 2D click, use x before y and keep every point inside the image width and
height. If there are `N` points, `p_label` is either one scalar or `N` labels.
For a 3D custom item, use one point per depth slice and keep its count equal to
`D`; an empty slice may receive a fallback point and negative/empty label.

The source's `random_click` reverses NumPy `[row,column]` indices to return
x/y. In contrast, `generate_click_prompt` for 3D obtains `torch.nonzero`
indices in row/column order and the loop reverses coordinates for visualization
only. This implementation asymmetry is a known uncertainty: if a custom class
supplies `pt` directly, follow the documented prompt convention and verify it
with the chosen model; if the source regenerates 3D prompts, do not “correct”
them solely from a visualization overlay.

`p_label=0` is a meaningful empty/background result from the source helper, not
proof that the mask is valid. Reject a malformed or unexpectedly blank target
before training.

## Custom dataset implementation checklist

A custom class should:

1. implement `__len__` and `__getitem__` with the argument/transform pattern
   expected by its selected registry branch;
2. pair image and label by a stable case id and preserve depth through every
   crop/resize;
3. return the required five fields above, including `image_meta_dict` for the
   current core loops;
4. document image/label dtype, class ids, channel order, prompt convention,
   and whether H/W are transformed to `image_size`/`out_size`;
5. add an import and exact case-sensitive branch if it is intended to be
   selectable by `-dataset`; documentation alone does not register a class;
6. validate a synthetic declaration before opening real files or allocating
   CUDA tensors.

The helper's success does not prove file decoding, NIfTI affine/orientation,
NRRD spacing, class semantics, prompt generation, checkpoint compatibility,
MONAI transform output, or CUDA execution.
