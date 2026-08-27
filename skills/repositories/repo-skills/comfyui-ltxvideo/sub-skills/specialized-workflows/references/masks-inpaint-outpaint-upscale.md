# Masks, inpaint/outpaint, pixel spatial upscaling, and blending

Use this reference when a specialized ComfyUI-LTXVideo workflow needs mask preprocessing, green inpaint composites, outpaint canvas extension, Laplacian seam blending, ingredients control, or creative pixel spatial upscaling.

## Mask preprocessing for latent-aware video masks

`LTXVPreprocessMasks` prepares video masks for LTXVideo latent masking.

Inputs and behavior:

- `masks` must be a 3D mask tensor shaped `(batch, height, width)`.
- `batch - 1` must be divisible by the VAE temporal scale factor. The first mask is usually the conditioning/reference frame; remaining masks are grouped by the temporal scale factor.
- `height` and `width` must be divisible by the VAE spatial scale factors.
- `invert_input_masks` flips mask polarity before other processing.
- `ignore_first_mask` defaults to true and zeros the first mask, which is useful when the first frame is a conditioning frame that should remain unmasked.
- `pooling_method` chooses how masks within each temporal group combine: `max`, `mean`, or `min`.
- `grow_mask` expands positive values or shrinks negative values through ComfyUI's mask grow operation; non-CPU masks may move through CPU for that step.
- `tapered_corners` smooths morphology when growing/shrinking.
- `clamp_min` and `clamp_max` clamp processed generated-frame masks after pooling/growth.

Use this node when a mask will drive latent-space masking or when a workflow needs consistent video mask timing. Resize masks before preprocessing so the batch/frame count and spatial dimensions satisfy the VAE rules.

## Fast mask dilation

`LTXVDilateVideoMask` dilates binary-like video masks with separable max-pooling.

- Provide either `mask` or `image_as_mask`. If both are missing, the node raises an error.
- If `image_as_mask` is used, channels are averaged to a mask.
- `spatial_radius` controls a `2 * radius + 1` spatial kernel.
- `temporal_radius` controls a `2 * radius + 1` temporal kernel.
- The result is thresholded at `> 0.5` to produce a float mask.

Use dilation to pad inpaint/outpaint regions and to create safer seam masks before blending. If edges look too wide or eat details, reduce spatial radius or adjust upstream mask polarity.

## Inpaint preprocessing with green composite

`LTXVInpaintPreprocess` creates the green conditioning composite expected by the in/outpainting IC-LoRA family.

- Inputs: `images` and `mask`.
- Active mask regions are replaced with RGB `#66FF00`.
- If the mask has a single frame and images have multiple frames, the mask broadcasts across the video.
- If image and mask frame counts differ, the node trims both to the shorter length.

Recipe:

1. Load/resize the source image or video frames to the workflow's conditioning resolution.
2. Load/resize the mask to the exact same spatial resolution and correct frame count.
3. Dilate or preprocess the mask if the filled region needs padding.
4. Use `LTXVInpaintPreprocess` to create the green reference composite.
5. Feed that composite into `LTXAddVideoICLoRAGuideAdvanced` when attention localization is helpful; otherwise use the basic guide.
6. Route sampler/decode/two-stage mechanics to [core-generation](../../core-generation/SKILL.md).

Common polarity rule: if the green appears on the area that should stay unchanged, invert the mask before inpaint preprocessing.

## Outpaint pattern

Outpaint workflows extend the canvas or frame boundary and then use the in-outpainting IC-LoRA to synthesize newly exposed regions.

Typical steps:

1. Resize the original media to the base generation multiple.
2. Pad or place it into a larger target canvas.
3. Create a mask where newly exposed border/canvas regions are active.
4. Resize masks and images to the same resolution.
5. Use `LTXVInpaintPreprocess` to produce a green composite for the unknown border.
6. Use IC-LoRA in-outpainting guidance and ordinary core sampling to fill the border.
7. Blend the generated result with the original source using `LTXVLaplacianPyramidBlend` to hide seams.

Use `LTXAddVideoICLoRAGuideAdvanced` if the border mask should also localize reference attention. Use the basic guide if the entire green composite should influence generation.

## Laplacian pyramid blending

`LTXVLaplacianPyramidBlend` blends two image/video tensors using a mask.

Inputs:

- `image_a`: first source image/video.
- `image_b`: second source image/video.
- `mask`: blend mask; white/1 selects `image_a`, black/0 selects `image_b`.
- `trim_to_shortest`: when true, trims `image_a`, `image_b`, and `mask` to the shortest frame count.
- `mask_low_res_dilation`: downscales the mask to a long side of 64, dilates it spatially, and upscales it before blending; use this to widen blend transitions.

Constraints:

- `image_a`, `image_b`, and `mask` must have the same spatial resolution.
- Frame counts must match unless `trim_to_shortest` is enabled.
- Internally, the implementation pads dimensions to powers of two for the Laplacian pyramid and processes chunks of frames.
- The verified compatible Kornia generation for this implementation is `kornia==0.7.1`; newer Kornia versions can remove the `pyramid.pad` import used by the node.

Blend use cases:

- Hide seams after outpaint or high-resolution stage replacement.
- Composite inpainted regions back into the original video.
- Smoothly merge creative pixel-upscaled output with a source crop when the mask defines a trusted area.

## Pixel spatial upscaler IC-LoRA

Pixel spatial upscaler LoRAs creatively re-render a low-resolution clip at a higher resolution. They synthesize detail rather than preserving every source pixel.

Use when:

- The user wants a 2x or 4x creative upscale from a draft clip.
- The source clip has locked composition/motion, and the second pass should invent high-frequency detail.
- Pixel-exact restoration is not required.

Recipe:

1. Choose the x2 or x4 pixel spatial upscaler LoRA for the desired scale.
2. Resize the low-resolution source/reference to the guide size expected by the graph, keeping aspect ratio intentional.
3. Load the LoRA through `LTXICLoRALoaderModelOnly` and connect its `latent_downscale_factor` to the guide.
4. Add the source clip as an IC-LoRA guide before final AV latent concatenation.
5. Generate at the target higher resolution using the core sampler/decode path.
6. Tune LoRA strength, guide strength, CFG, step count, and prompt detail for fidelity versus creative texture.

Troubleshooting:

- If output is too different from the source, lower guide/LoRA strength or reduce creative prompt pressure.
- If output copies low-res artifacts too strongly, raise prompt detail or allow stronger IC-LoRA influence.
- If shape errors occur, check `latent_downscale_factor` divisibility in [IC-LoRA recipes](ic-lora-recipes.md).

## Ingredients IC-LoRA

Ingredients workflows use a reference ingredient/object image as a controllable source of content.

- Use the ingredients LoRA through `LTXICLoRALoaderModelOnly`.
- Resize the reference image to a guide-compatible resolution.
- Add it as an IC-LoRA guide.
- Let the prompt specify scene placement, action, and style. The guide contributes ingredient identity/appearance but is not a guarantee of exact spatial placement.

If the user asks for exact object placement or region control, combine the ingredients recipe with masks/advanced attention or route ordinary layout/sampling decisions to the core and prompt sub-skills.

## Native execution boundary

Mask utilities can be reasoned about statically, but full inpaint/outpaint/upscale workflows still require ComfyUI, CUDA, model weights, IC-LoRA weights, and source media. Do not claim generation quality or execute native workflows from this sub-skill drafting context.
