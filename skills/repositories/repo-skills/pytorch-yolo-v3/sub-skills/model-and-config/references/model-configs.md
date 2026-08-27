# Model configuration and class-name guidance

Use this reference for Darknet cfg compatibility, class-count edits, names files, and resolution checks.

## Known bundled cfg variants

| cfg path in a user checkout | Parse result | Construction result in this repo | Notes |
| --- | ---: | --- | --- |
| `cfg/yolov3.cfg` | 108 blocks, including 3 `yolo` blocks | Supported: constructs 107 modules | COCO-style YOLOv3 config with `classes=80` and three detection heads. |
| `cfg/yolo.cfg` | 33 blocks, including `region` and `reorg` | Unsupported: `create_modules` raises `AssertionError` after printing `Something I dunno` | YOLOv2-style config; parses but is not implemented by this repo's constructor. |
| `cfg/yolo-voc.cfg` | 33 blocks, including `region` and `reorg` | Unsupported: `create_modules` raises `AssertionError` after printing `Something I dunno` | VOC-style YOLOv2 config; parseable but not constructible here. |
| `cfg/tiny-yolo-voc.cfg` | 17 blocks, including `region` | Unsupported: `create_modules` raises `AssertionError` after printing `Something I dunno` | Tiny YOLO VOC-style config; parseable but not constructible here. |

`region` and `reorg` are the critical unsupported block types for the non-YOLOv3 cfgs. A `ReOrgLayer` class exists in the model file, but `create_modules` does not dispatch `reorg`, and it does not implement `region` at all.

## Names files and class counts

Known names-file counts:

- `data/coco.names`: 80 nonempty class names.
- `data/voc.names`: 20 nonempty class names.

For `cfg/yolov3.cfg`, all three `[yolo]` blocks declare `classes=80`, so `data/coco.names` is the expected names file. VOC names have 20 entries and do not match unmodified `cfg/yolov3.cfg`.

Before loading weights or running detection with a modified class set, check all of these together:

1. The names file has exactly `N` nonempty class-name lines.
2. Every `[yolo]` block has `classes=N`.
3. The convolutional block immediately before each `[yolo]` block has `filters=(N + 5) * M`, where `M` is the number of mask entries for that yolo head. In the YOLOv3 cfg, each head has three mask entries, so the common formula is `filters=3 * (N + 5)`.
4. All three YOLOv3 detection heads are updated consistently.
5. Any weight file is compatible with the edited architecture. Original COCO weights match the 80-class heads; they should not be assumed to load after changing class counts or final filters.

Use the bundled inspector:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg cfg/yolov3.cfg --names data/coco.names
```

For a custom class set:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg <custom.cfg> --names <custom.names>
```

The inspector reports detection-head classes, mask counts, expected filters, actual preceding convolution filters, and names-file count mismatches.

## Resolution constraints

The repo's documented detector resolution rule is: input resolution must be greater than 32 and a multiple of 32. Keep both `width` and `height` valid integers. For this implementation, square dimensions are the safest choice because detection code commonly uses `height` as the model input dimension.

Examples of valid dimensions: `320`, `416`, `608`.

Invalid or risky dimensions:

- `32` or smaller: too small for the detector's downsampling structure.
- Values not divisible by 32, such as `300` or `500`: feature map scales will not align cleanly.
- Width/height disagreement without a verified preprocessing and forward path: this repo's YOLO transform reads the configured height as the input dimension.

The bundled `cfg/yolov3.cfg` declares valid 320-by-320 net dimensions and can be constructed by `Darknet(cfgfile)`.

## Weight compatibility checklist

Before calling `load_weights(weightfile)`:

- Confirm the cfg constructs successfully with `Darknet(cfgfile)`.
- Confirm the cfg class/filter relationship matches the intended names file.
- Confirm the weight file is local and was produced for the same architecture family and class count.
- Treat header-only success as insufficient; shape mismatches can appear while copying later convolutional tensors.
- If only inspecting cfg compatibility, do not call `load_weights` and do not download weights.

## Decision rules for common requests

- "Can I use `yolo-voc.cfg`?" Answer: it parses, but this repo's `create_modules` cannot build it because of `region` and `reorg` blocks. Use a supported YOLOv3-style cfg or patch and verify constructor support before relying on it.
- "I changed to K classes." Answer: update every `[yolo]` `classes` value, update each preceding detection convolution's `filters`, provide a K-line names file, and use weights compatible with the edited heads.
- "Why does `Darknet(cfgfile)` print `Something I dunno`?" Answer: an unsupported cfg block reached the fallback branch in `create_modules`; inspect block counts and unsupported types with the bundled script.
