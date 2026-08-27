---
name: variable-shapes-video
description: "Routes vit-pytorch variable-resolution NaViT batches, nested
  tensor variants, 1D/3D/N-D tensors, and video transformer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Variable Shapes and Video

Use this sub-skill when a user needs vit-pytorch guidance for variable spatial sizes, non-image tensor ranks, or video inputs. Route prompts here when they mention `NaViT`, `na_vit_nested_tensor`, `na_vit_nested_tensor_3d`, `vit_3d`, `simple_vit_3d`, `cct_3d`, `vivit`, `vivit_with_moss`, `vit_1d`, `simple_vit_1d`, `vit_nd`, `vit_nd_pope`, `vit_nd_rotary`, `accept_video_wrapper`, variable-resolution grouping, max token budgets, frame patching, or N-D patch grids.

## Route by user intent

- **Variable-resolution images in one forward**: use `vit_pytorch.na_vit.NaViT`. Read [workflows](references/workflows.md#navit-variable-resolution-image-batches) before choosing manual `List[List[Tensor]]` grouping or `group_images=True` auto grouping with `group_max_seq_len`.
- **Nested tensor NaViT**: use `vit_pytorch.na_vit_nested_tensor.NaViT` for a flat list of image tensors, or `vit_pytorch.na_vit_nested_tensor_3d.NaViT` for a flat list of `(channels, frames, height, width)` volumes, only after checking PyTorch nested/jagged support. Read [nested tensor caveats](references/workflows.md#nested-tensor-navit-variants) and [troubleshooting](references/troubleshooting.md#nested-tensor-version-and-input-caveats).
- **3D and video classifiers**: use `vit_pytorch.vit_3d.ViT`, `vit_pytorch.simple_vit_3d.SimpleViT`, `vit_pytorch.cct_3d.CCT`, `vit_pytorch.vivit.ViViT`, or `vit_pytorch.vivit_with_moss.ViViT` for inputs shaped `(batch, channels, frames, height, width)`. Read [video layouts](references/workflows.md#3d-and-video-transformer-families) before setting `frames`, `frame_patch_size`, and `image_patch_size`.
- **Video wrapper around an image model**: use `vit_pytorch.accept_video_wrapper.AcceptVideoWrapper` when the user already has an image backbone and wants to run it per frame, optionally restoring time as an output dimension, adding time positional embeddings, or applying MOSS over patch-token outputs.
- **1D or N-D tensors**: use `vit_pytorch.vit_1d.ViT`, `vit_pytorch.simple_vit_1d.SimpleViT`, `vit_pytorch.vit_nd.ViTND`, `vit_pytorch.vit_nd_pope.ViTND`, or `vit_pytorch.vit_nd_rotary.ViTND`. Read [1D and N-D routing](references/workflows.md#1d-and-n-d-tensor-families) for input layouts, tuple length rules, and patch-grid outputs.

## Boundaries

This sub-skill owns variable-resolution image grouping, max sequence length packing, patch and grid position handling, video frame/spatial patch shapes, N-D patching, and nested-tensor caveats.

Route elsewhere instead of duplicating guidance:

- Pure image-only architecture selection, standard square/non-square image classifier choice, and image architecture comparisons belong to the image-architecture route unless the prompt asks about variable sizes or non-image ranks.
- Loss-based pretraining, distillation, masked modeling, DINO/EsViT, MAE/SimMIM/MPP, or adaptation wrappers belong to the pretraining/adaptation route.
- Attention inspection-only wrappers such as `Recorder` and `Extractor` belong to the introspection/customization route unless they are only incidental to a variable-shape or video workflow.

## Operating rules for future agents

1. **Normalize the tensor layout before constructing a model.** NaViT images are unbatched `(channels, height, width)` tensors in Python lists; video/3D models consume `(batch, channels, frames, height, width)`; 1D models consume `(batch, channels, seq_len)`; N-D models consume `(batch, channels, *input_shape)`.
2. **Check divisibility before running.** Height and width must be divisible by `patch_size` or `image_patch_size`; `frames` must be divisible by `frame_patch_size`; each N-D dimension must be divisible by its corresponding patch dimension. See [troubleshooting](references/troubleshooting.md#patch-divisibility-and-position-grid-errors).
3. **For NaViT, compute token counts before grouping.** A standard NaViT image contributes `(height // patch_size) * (width // patch_size)` tokens before optional token dropout. `group_images=True` greedily preserves input order and starts a new group when adding the next image would exceed `group_max_seq_len`; it cannot rescue one image whose token count is already too large.
4. **Separate temporal and spatial patch sizes.** `frame_patch_size` patches along the frame axis; `image_patch_size` patches height and width. Do not swap them, and do not use `(batch, frames, channels, height, width)` with these modules.
5. **Treat nested tensor paths as version-sensitive.** Prefer standard `na_vit.NaViT` for broadly portable examples. Use nested tensor variants only after a small runtime probe confirms the installed PyTorch supports the required nested/jagged operations.
6. **Use the bundled smoke helper for confidence.** After installing `vit-pytorch`, run:

   ```bash
   python sub-skills/variable-shapes-video/scripts/smoke_variable_shapes_video.py
   ```

   The helper imports the installed package, uses tiny CPU tensors, and does not read repository source files.

## References

- [Grouping rules, layouts, and supported families](references/workflows.md)
- [Shape, grouping, version, and wrapper troubleshooting](references/troubleshooting.md)
- [CPU smoke helper](scripts/smoke_variable_shapes_video.py)
