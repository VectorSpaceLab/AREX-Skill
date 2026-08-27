# DINO model architecture and compatibility

## Input and output contract

`DINO.forward` accepts a `NestedTensor` containing a batch tensor shaped
`[batch, 3, H, W]` and a boolean padding mask shaped `[batch, H, W]`. A list of
images or a tensor is wrapped into a `NestedTensor` by the model. The backbone
returns an ordered list of feature `NestedTensor`s and matching positional
encodings. Each feature has shape `[batch, C_l, H_l, W_l]`; masks are resized to
that spatial size.

The input projections map each selected backbone feature to the transformer's
`hidden_dim` (default 256) with a 1x1 convolution and GroupNorm. If the config
requests more feature levels than the backbone returns, DINO creates extra
levels with stride-2 3x3 projections from the last source. Therefore:

- `num_feature_levels` must be at least the number of returned backbone levels
  when multi-level deformable encoding is used;
- additional levels are derived, not additional backbone outputs;
- the transformer receives `L = num_feature_levels` flattened levels, each
  `[batch, H_l*W_l, hidden_dim]`, with concatenated length
  `S = sum_l(H_l*W_l)`;
- `input_spatial_shapes` is `[L,2]` containing `(H_l,W_l)` and
  `input_level_start_index` is `[L]` containing cumulative flattened starts.

The deformable attention module takes query `[N,Lq,C]`, flattened input
`[N,S,C]`, reference points `[N,Lq,L,2]` or `[N,Lq,L,4]`, spatial shapes,
level starts, and an optional padding mask `[N,S]`. It returns
`[N,Lq,C]`. The CUDA implementation is used by both encoder and decoder in
the standard DINO transformer; the PyTorch core in
`functions/ms_deform_attn_func.py` is a debug/reference implementation, not an
approved performance or compatibility fallback for a normal run.

For ordinary detection, the final model output contains:

| Key | Shape | Meaning |
|---|---|---|
| `pred_logits` | `[B, num_queries, num_classes]` | sigmoid focal classification logits |
| `pred_boxes` | `[B, num_queries, 4]` | normalized `cx,cy,w,h` in `[0,1]` |
| `aux_outputs` | optional list | per-decoder-layer dictionaries with the same two keys |
| `dn_meta` | metadata or `None` | denoising bookkeeping, not a prediction tensor |

With `two_stage_type='standard'`, intermediate encoder outputs may also be
returned (`interm_outputs`, and related matching data). With `masks=True`, the
segmentation wrapper adds `pred_masks` and extra postprocessors; that branch
requires valid segmentation data. These are model outputs, not a substitute
for the input target schema.

`num_queries` is the maximum number of detection slots (the released configs
use 900 and select 300 for post-processing). `num_classes` is the classifier
width described in [data formats](data-formats.md), and the criterion uses an
internal no-object sentinel. A checkpoint/config pair must agree on these
structural dimensions.

## Released config families

All shipped `config/DINO/*.py` files inherit `coco_transformer.py`, whose
augmentation defaults are train scales 480..800, `max_size=1333`, crop-branch
resize scales 400/500/600 and crop range 384..600. The principal families are:

| Config family | Backbone | returned indices | backbone channels | feature levels | notable setup |
|---|---|---:|---:|---:|---|
| `DINO_4scale.py` | `resnet50` | `[1,2,3]` | `[512,1024,2048]` | 4 | one extra projected level; 256-d model, 8 heads, 6+6 layers |
| `DINO_5scale.py` | `resnet50` | `[0,1,2,3]` | `[256,512,1024,2048]` | 5 | one extra projected level; batch size 1 in the released config |
| `DINO_4scale_swin.py` | `swin_L_384_22k` | `[1,2,3]` | implementation-provided Swin channels | 4 | checkpoint and optional gradient checkpointing required for the backbone branch |
| `DINO_4scale_convnext.py` | `convnext_xlarge_22k` | `[1,2,3]` | implementation-provided ConvNeXt dims | 4 | a compatible pretrained backbone path is required |

The `backbone.py` contract accepts ResNet-50/101, the listed Swin variants, and
`convnext_xlarge_22k`. For ResNet, `return_interm_indices` must be exactly one
of `[0,1,2,3]`, `[1,2,3]`, or `[3]`; its length must match the returned channel
list. `lr_backbone > 0` is required by `build_backbone`, even when most
parameters are frozen. Swin and ConvNeXt require their own compatible model
implementation and pretrained weights; downloading those weights is outside
this skill.

## Structural setup checks

Before a model build, inspect the resolved config (including `_base_` and
command-line overrides) and verify:

1. `hidden_dim % nheads == 0`; a power-of-two per-head dimension is preferred
   by the CUDA kernel. The released 256/8 setting gives 32 channels per head.
2. `return_interm_indices` is one of the supported lists and its length does
   not exceed `num_feature_levels`.
3. `num_feature_levels > 1` implies deformable encoder/decoder, which the DINO
   builder enables. `num_feature_levels == 1` is incompatible with a standard
   two-stage config (`two_stage_type` must be `no`).
4. `query_dim == 4`, `enc_n_points` and `dec_n_points` are positive, and
   `decoder_module_seq` contains exactly `['sa','ca','ffn']` in some order.
5. `num_classes` covers every category ID used by the dataset under the chosen
   indexing policy; `dn_labelbook_size` is large enough for the class setup.
6. `args.masks` matches the data branch: instance polygons/RLE or panoptic
   segment PNGs must be available when mask losses are enabled.
7. A checkpoint's classifier, query, backbone, transformer, and feature-level
   dimensions match the resolved config. A non-strict load may hide a bad
   classifier head but does not make it semantically compatible.

`util/slconfig.py` executes Python config files, recursively resolves `_base_`
files, rejects syntax errors and duplicate base keys, and supports command-line
`KEY=VALUE` overrides through `DictAction`. Parse configs in a trusted source
checkout only: do not treat an arbitrary untrusted config as inert data.

## CUDA extension dependency

`models/dino/ops/setup.py` builds a CUDA extension named
`MultiScaleDeformableAttention` from C++ and `.cu` sources when
`torch.cuda.is_available()` and PyTorch's `CUDA_HOME` are both available. The
Python function wrapper calls `ms_deform_attn_forward` and
`ms_deform_attn_backward`; the module checks that `d_model` is divisible by
`n_heads` and warns when the per-head dimension is not a power of two.

The extension is a required runtime dependency for the repository's standard
multi-scale deformable transformer. It must be compiled for the active
PyTorch/CUDA ABI and an architecture supported by the target GPU, then
verified numerically with the repo's CUDA test. A CPU-only machine can inspect
configs and run the pure-PyTorch reference function in isolation, but it
cannot establish that DINO's required CUDA path works. Do not call that a
successful DINO backend setup.
