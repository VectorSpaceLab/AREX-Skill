# Model/config troubleshooting

Use this reference when cfg parsing, model construction, names checks, or Darknet binary weight loading fails.

## Quick diagnostic command

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg <cfg-file> --names <names-file>
```

Add `--build-model` only when the user wants to verify actual `Darknet(cfgfile)` construction in the current Python environment:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg <cfg-file> --build-model
```

The script does not download weights, open cameras, run inference, draw images, or write outputs.

## Symptoms and fixes

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `cfg` file is missing | Wrong path or checkout does not include the expected cfg | Ask for the correct local file. Use `--repo-root <repo-root> --cfg <relative-or-absolute-cfg>` with the bundled inspector. |
| Names file is missing | Wrong path or user has not supplied class names | Ask for a local `.names` file. Do not download one from this sub-skill. |
| `Darknet(cfgfile)` prints `Something I dunno` and raises `AssertionError` | The cfg parsed, but `create_modules` reached an unsupported block type | Inspect block types. `cfg/yolo.cfg`, `cfg/yolo-voc.cfg`, and `cfg/tiny-yolo-voc.cfg` are known to contain `region` and/or `reorg`, which are not implemented by this constructor. |
| User supplies `yolo-voc.cfg` and asks why construction fails | `yolo-voc.cfg` is YOLOv2/VOC-style and includes both `region` and `reorg` blocks | Explain that `parse_cfg` can read it but `create_modules` cannot build it. Use a supported YOLOv3-style cfg or implement and verify missing block support before construction. |
| Names count does not match cfg classes | `.names` line count differs from the `[yolo]` `classes` value | Edit the cfg or names file so each `[yolo]` block and the names file agree on the same class count. |
| `filters` mismatch before a YOLO head | Class count changed without updating the final convolution filters | For each `[yolo]` block, set the immediately preceding convolution `filters` to `(classes + 5) * number_of_mask_entries`. For YOLOv3 heads with 3 masks, use `3 * (classes + 5)`. |
| Resolution error or strange feature-map behavior | `width` or `height` is not greater than 32 or not divisible by 32 | Use valid dimensions such as 320, 416, or 608. Keep square dimensions unless the full preprocessing and forward path has been verified. |
| Missing weight file | `load_weights` was called with a path that does not exist | Ask the user for a local weight file. This sub-skill must not download weights. |
| Weight loading fails with tensor shape or copy errors | Weight file architecture does not match cfg filters/classes/layers, or file is truncated | Re-check cfg/names/filter compatibility. Use weights produced for the same cfg, especially after class-count edits. |
| Weight loading appears to succeed but detections are wrong after class edits | Original pretrained weights are tied to old detection-head shapes/classes | Do not assume COCO weights are usable with custom class heads. A compatible trained weight file is required for reliable detection. |
| PyTorch 0.3 failures | The repo targets PyTorch 0.4-era behavior and explicitly warns that PyTorch 0.3 breaks the detector | Use a compatible PyTorch runtime or patch the code deliberately. |
| Modern PyTorch warnings around `Variable`, `.data`, or upsampling | The code uses legacy PyTorch idioms | Treat warnings separately from cfg compatibility. Avoid changing model code unless the user asked for modernization and downstream behavior can be verified. |
| CPU/GPU confusion in forward | `Darknet.forward(self, x, CUDA)` expects an explicit CUDA flag and helper code also uses a global CUDA flag | Match the boolean flag to the tensor/device path. Do not use this sub-skill for full image preprocessing or postprocessing. |

## Hard-case guidance

### Case 1: VOC cfg construction failure

If a user provides `cfg/yolo-voc.cfg` or `cfg/tiny-yolo-voc.cfg` and asks for `Darknet(cfgfile)`, do not treat successful parsing as compatibility. These cfg files contain unsupported block types. Explain the two-stage behavior:

1. `parse_cfg(cfgfile)` returns blocks.
2. `create_modules(blocks)` fails when it reaches `region` or `reorg`, printing `Something I dunno` and raising `AssertionError`.

Use the bundled script to show the unsupported block counts.

### Case 2: Custom classes before loading weights

If a user changes from 80 classes to a custom count, inspect before loading any weights:

1. Count nonempty lines in the custom names file.
2. Check every `[yolo]` block's `classes` value.
3. Check each immediately preceding convolution's `filters` value.
4. Warn that old COCO weights are not compatible with modified detection heads unless the loading strategy intentionally skips or replaces those heads.

Do not download replacement weights and do not begin training from this sub-skill.
