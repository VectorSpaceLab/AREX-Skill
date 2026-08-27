# Advanced Controls Troubleshooting

## Planner rejects style weights

**Symptom:** `plan_advanced_args.py` reports that `--style-weight` count does not match `--style` count.

**Likely cause:** The source parser would accept the command, but `sum_style_losses(...)` zips style images and weights and can ignore extras. This produces misleading interpolation.

**Recovery:** Provide one raw weight per style image. The absolute scale does not matter because the source normalizes weights; `7 3`, `0.7 0.3`, and `70 30` represent the same ratio.

## Multiple styles unexpectedly look like one style

**Symptoms:** Output seems dominated by the first style; changing a later weight has no effect.

**Likely causes:**

- A style filename and weight list mismatch caused truncation.
- All style weights normalized to zero because their sum was not positive.
- The base command used a helper that emitted equal weights, but the user expected custom interpolation.

**Recovery:** Rebuild the advanced flag fragment with `scripts/plan_advanced_args.py`, then splice the emitted `--style_imgs_weights` into the final command.

## Masked style transfer crashes or affects the wrong region

**Symptoms:** missing-file error for a mask, raw Python error around `zip(..., masks)`, output ignores mask boundaries, or all pixels become invalid.

**Likely causes:**

- `--style_mask` was supplied without `--style_mask_imgs`.
- Mask filenames were placed in the style directory; the source reads them from `--content_img_dir`.
- The number of masks does not match the number of style images.
- A mask is all black, producing a divide-by-zero during normalization.

**Recovery:** Put masks next to the content image or set `--content_img_dir` to their directory, provide one mask per style, and inspect mask values before running a long optimization. For foreground/background transfer, use complementary masks such as `face_mask.png` and `face_mask_inv.png`.

## Original colors do not behave as expected

**Symptoms:** `--color_convert_time before` appears to have no different effect from the default, or colors still shift after style transfer.

**Likely cause:** The source parses `--color_convert_time`, but the implementation calls `convert_to_original_colors(...)` only after stylization. The `before` mode is not implemented in the inspected source.

**Recovery:** Treat `--original_colors --color_convert_type <space>` as an after-stylization luminance/chroma conversion. Try `yuv`, `ycrcb`, `luv`, or `lab` and compare outputs; do not rely on `before` unless a refreshed checkout changes the code.

## Layer or layer-weight changes silently do nothing

**Symptoms:** A layer weight tweak has no visible effect, or output differs less than expected.

**Likely causes:**

- Weight count does not match layer count; the source zips lists.
- A misspelled layer name is not caught until graph lookup time.
- Weight ratios were changed without accounting for internal normalization.

**Recovery:** Validate list counts with the planner, use VGG layer names present in the source (`conv1_1` through `conv5_4`, `relu1_1` through `relu5_4` as constructed), and change one layer group per run.

## L-BFGS memory errors

**Symptoms:** process is killed, TensorFlow allocation errors, or the run stalls before first output.

**Likely causes:** L-BFGS stores more optimizer state, large `--max_size` increases tensor memory, and GPU default may select a constrained device.

**Recovery:** Lower `--max_size`, switch to `--optimizer adam`, lower iterations for smoke tests, or run on a machine with more VRAM/RAM. For CPU smoke checks, explicitly pass `--device /cpu:0`.

## Random initialization is not reproducible

**Symptoms:** two random-initialized runs differ when the user expected identical output.

**Likely causes:** `--seed` was omitted or changed; only the NumPy noise image uses that seed, while environment-level nondeterminism may still affect TensorFlow execution.

**Recovery:** Set `--init_img_type random --seed <integer>`, keep TensorFlow/device settings constant, and compare the saved output metadata for both runs.
