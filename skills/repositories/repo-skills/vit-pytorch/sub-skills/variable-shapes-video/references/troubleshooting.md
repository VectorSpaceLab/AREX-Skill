# Troubleshooting: Shapes, Grouping, Versions, and Video Wrappers

## Purpose

Use this guide when a vit-pytorch variable-shape, N-D, 3D, or video workflow fails before or during a forward pass. Most failures are caused by a wrong input layout, patch divisibility mismatch, a NaViT grouping budget mistake, or a version-sensitive nested tensor path.

## Patch divisibility and position-grid errors

Symptoms:

- `AssertionError: Image dimensions must be divisible by the patch size.`
- `AssertionError: height and width ... must be divisible by patch size ...`
- Einops shape errors mentioning unmatched `(h p1)`, `(w p2)`, or `(f pf)` dimensions.
- Index errors or shape mismatch after patching, especially in NaViT positional embeddings.

Likely causes:

- Height or width is not divisible by `patch_size` / `image_patch_size`.
- Video `frames` is not divisible by `frame_patch_size`.
- A NaViT input image is larger than the configured `image_size`, so patch position indices exceed the model's factorized position tables.
- For N-D models, one `input_shape[i]` is not divisible by `patch_size[i]`.

Recovery:

1. Print the exact runtime tensor shape before constructing or calling the model.
2. For NaViT images, use tensors shaped `(channels, height, width)` and check:

   ```python
   assert height <= image_size_height
   assert width <= image_size_width
   assert height % patch_size == 0
   assert width % patch_size == 0
   ```

3. For 3D/video tensors, use `(batch, channels, frames, height, width)` and check:

   ```python
   assert frames % frame_patch_size == 0
   assert height % image_patch_height == 0
   assert width % image_patch_width == 0
   ```

4. For N-D tensors, expand integers to tuples of length `ndim`, then check every dimension-patch pair.
5. Resize, crop, pad, or change patch sizes before the forward pass; do not expect the model to auto-pad arbitrary dimensions.

## Grouped batch exceeds max sequence length

Symptoms:

- `AssertionError: image with dimensions ... exceeds maximum sequence length` from `group_images_by_max_seq_len`.
- Out-of-memory or very slow attention when passing a flat list to `NaViT` without `group_images=True`.
- The output has the right number of rows but a user expected different group boundaries.

Likely causes:

- A single image has more tokens than `group_max_seq_len`:

  ```text
  image_tokens = (height // patch_size) * (width // patch_size)
  ```

- A flat `List[Tensor]` was passed with `group_images=False`; standard NaViT treats it as one packed group.
- The user expected auto grouping to sort or bin-pack images, but the helper is greedy and input-order preserving.
- During training with token dropout, the grouping helper estimates post-dropout sequence lengths; in eval mode it uses full token counts.

Recovery:

1. Compute per-image token counts before calling the model.
2. If one image exceeds the max, use a larger patch size, lower resolution, higher `group_max_seq_len`, or training-time token dropout if that is scientifically appropriate. Regrouping cannot fit a single over-budget image.
3. If only the sum is too large, set `group_images=True` and choose a `group_max_seq_len` that fits memory.
4. If order matters, remember that auto grouping preserves the original image order. Manual grouping returns logits in group order, then inner-list order.
5. For reproducible training with token dropout, set seeds and validate grouping on a tiny batch before launching a long run.

## Variable-resolution grouping order mistakes

Symptoms:

- Labels no longer align with logits after manual grouping.
- Predictions appear to be permuted across images.
- A data loader supplies nested lists but the target list remains flat or sorted differently.

Likely causes:

- Manual `List[List[Tensor]]` grouping changed order but labels were not grouped in the same order.
- A later collation step flattened images by size bucket rather than by original sample order.
- A user expected NaViT to return one row per group; it returns one row per image.

Recovery:

1. Carry `(image, label, sample_id)` together through grouping.
2. For manual grouping, flatten labels with the exact same loop used to flatten images: group order first, inner-list order second.
3. For auto grouping, keep the original flat order; the helper preserves it.
4. Assert `logits.shape[0] == len(flat_images)` on every smoke batch.

## Frame patch size versus image patch size confusion

Symptoms:

- `AssertionError: Frames must be divisible by frame patch size`.
- `AssertionError: Image dimensions must be divisible by the patch size` for a video model.
- Einops errors involving `(f pf)` after the user thought `image_patch_size` controlled frames.
- The user passes video shaped `(batch, frames, channels, height, width)` and sees a channel or patching mismatch.

Likely causes:

- `frame_patch_size` was accidentally set to a spatial patch size such as `16` when there are only `8` frames.
- `image_patch_size` was accidentally set to a temporal patch such as `2` when height/width patching should be `16`.
- Tensor dimensions are ordered incorrectly.
- The constructor's `frames` does not equal the frame count used in the actual input.

Recovery:

1. Normalize the tensor with `video = video.permute(0, 2, 1, 3, 4)` if the current layout is `(batch, frames, channels, height, width)`.
2. Use names that separate axes:

   ```python
   model = ViT(
       image_size = 128,
       frames = 16,
       image_patch_size = 16,  # patches height/width
       frame_patch_size = 2,   # patches time
       ...
   )
   ```

3. Check the derived patch grid before forward:

   ```python
   frame_tokens = frames // frame_patch_size
   spatial_tokens = (height // image_patch_size) * (width // image_patch_size)
   total_tokens = frame_tokens * spatial_tokens
   ```

4. Run the bundled smoke helper on tiny data, then scale dimensions one axis at a time.

## ViViT-specific shape and mask failures

Symptoms:

- `variant = ... is not implemented`.
- `Spatial and temporal depth must be the same for factorized self-attention`.
- Mask shape errors around `reduce(mask, 'b (f patch) -> b f', patch=frame_patch_size)`.
- Import code copied from a README snippet fails to find `ViT` inside `vit_pytorch.vivit`.

Likely causes:

- `variant` is not one of `'factorized_encoder'` or `'factorized_self_attention'`.
- `variant='factorized_self_attention'` but `spatial_depth != temporal_depth`.
- The temporal mask length is not divisible by `frame_patch_size` or does not match the original frame count.
- The installed source exposes `ViViT` but not the README alias `ViT`.

Recovery:

1. Prefer a robust import pattern when writing reusable examples:

   ```python
   import importlib
   vivit_mod = importlib.import_module('vit_pytorch.vivit')
   ViViT = getattr(vivit_mod, 'ViViT', getattr(vivit_mod, 'ViT', None))
   assert ViViT is not None
   ```

2. Keep `spatial_depth == temporal_depth` for `factorized_self_attention`.
3. If using a mask, start from a boolean tensor whose length is the original number of frames and is divisible by `frame_patch_size`.
4. For CPU smoke tests, set `use_flash_attn=False` to use the non-SDPA path after import succeeds.

## ViViT with MOSS failures

Symptoms:

- `AssertionError: MOSS local dimensions must be odd`.
- `AssertionError: mask cannot be passed if MOSS is causal`.
- Shape errors while reshaping patch tokens to a `(frame, height, width)` grid.

Likely causes:

- One of `moss_local_time`, `moss_local_height`, or `moss_local_width` is even.
- `moss_causal=True` and the forward call supplies `mask`.
- `image_size` / `image_patch_size` does not match the actual video height/width, so the patch-token grid size is wrong.

Recovery:

1. Use odd local MOSS sizes, for example `3, 3, 3`.
2. Either remove `mask` or construct with `moss_causal=False` when a mask is required.
3. Confirm `patch_grid_height = height // image_patch_height` and `patch_grid_width = width // image_patch_width` match the configured model.
4. Smoke-test without MOSS first using plain `vivit.ViViT`; add MOSS only after the base video layout works.

## CCT 3D sequence length and positional embedding mismatches

Symptoms:

- Tensor-size mismatch when adding positional embeddings in `cct_3d.CCT`.
- A CCT 3D model works for one video size but fails for another.

Likely causes:

- `CCT` computes `sequence_length` from `img_size`, `num_frames`, and tokenizer convolution/pooling settings during construction.
- Actual video dimensions or frame count differ from that construction-time size.
- Positional embedding is `'sine'` or `'learnable'`, so sequence length must match.

Recovery:

1. Set `img_size` and `num_frames` to the exact height/width/frame count used by the input.
2. Keep tokenizer temporal and spatial stride/pooling settings fixed between construction and inference.
3. If intentionally accepting variable sizes, investigate `positional_embedding='none'` and validate the resulting classifier behavior with a small controlled test.

## 1D and N-D tensor shape failures

Symptoms:

- `AssertionError` from `seq_len % patch_size` in 1D models.
- `Expected tuple of length ...` in N-D models.
- `Input dimension i (...) must be divisible by patch size (...)`.
- `ndim must be between 1 and 7`.
- `return_embed=True` gives a patch-grid shape the user misreads as original input resolution.

Likely causes:

- 1D input is shaped `(batch, seq_len, channels)` instead of `(batch, channels, seq_len)`.
- `input_shape` or `patch_size` tuple length differs from `ndim`.
- The user expects the embedding grid to have original spatial dimensions rather than patch counts.

Recovery:

1. Rearrange 1D inputs to `(batch, channels, seq_len)`.
2. Convert all N-D sizes to explicit tuples before model construction.
3. Check `len(input_shape) == len(patch_size) == ndim`.
4. For `vit_nd_pope` or `vit_nd_rotary` with `return_embed=True`, expect:

   ```text
   output shape = (batch, *(input_dim // patch_dim for each axis), dim)
   ```

5. Use the standard `vit_nd.ViTND` route unless the user specifically asks for PoPE/RoPE or patch-grid embeddings.

## Nested tensor version and input caveats

Symptoms:

- Warnings or errors about prototype nested tensors, jagged layout, unsupported nested tensor operators, or scaled-dot-product attention.
- Standard NaViT works but `na_vit_nested_tensor` fails on the same images.
- Training-mode nested NaViT raises a comparison error involving `token_dropout_prob`.
- 3D nested NaViT error text mentions dimensions confusingly.

Likely causes:

- The README notes nested tensor NaViT was tested on PyTorch 2.5; older or custom builds may not cover the required nested/jagged operations.
- The nested variants expect a flat list, not grouped `List[List[Tensor]]`.
- `token_dropout_prob` was left as `None` in training mode in a version whose forward path compares it to zero.
- A volume is not shaped `(channels, frames, height, width)` or exceeds `max_frames` / `image_size` position tables.

Recovery:

1. First prove the same data with standard `vit_pytorch.na_vit.NaViT`.
2. Check runtime support with a tiny nested tensor forward before using nested tensors in a long job.
3. Use a flat list of tensors for nested variants.
4. Pass `token_dropout_prob=0.0` when constructing a nested model that will be in training mode but should not drop tokens.
5. Fall back to standard NaViT if nested tensor backend errors are not directly relevant to the user's research question.

## AcceptVideoWrapper output and MOSS mistakes

Symptoms:

- Time dimension is missing or restored on the wrong output.
- `received video with ... frames but time_seq_len ... is too low`.
- `dim_emb must be passed in` or `dim_emb and time_seq_len must be set`.
- MOSS path fails when splitting CLS tokens from patch tokens.

Likely causes:

- `output_pos_add_pos_emb` points at logits instead of embeddings.
- The wrapped image net returns a scalar/loss or nested structure the user did not account for.
- `add_time_pos_emb=True` without sufficient `time_seq_len`.
- The selected embedding output does not contain one token per image patch plus optional CLS/register tokens.

Recovery:

1. Run the image model on one frame batch first and inspect its exact output tree.
2. Choose `output_pos_add_pos_emb` only after confirming which flattened output is the embedding tensor.
3. If adding time positional embeddings, set `dim_emb` to the embedding dimension and `time_seq_len` to at least the maximum video length.
4. For MOSS, provide or verify `patch_size` and assert:

   ```python
   num_patch_tokens = (height // patch_h) * (width // patch_w)
   assert embed.shape[-2] >= num_patch_tokens
   ```

5. If the image net returns only logits, use the wrapper for framewise logits/features without MOSS, or wrap an extractor that returns patch embeddings.
