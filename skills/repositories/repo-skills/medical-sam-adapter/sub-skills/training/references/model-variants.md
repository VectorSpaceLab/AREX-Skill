# Model and encoder variants

`utils.get_network` selects a registry from `-net` and looks up the exact,
case-sensitive `-encoder` string. A registry check only proves that a name is
listed; it does not load a checkpoint or prove tensor compatibility.

## Adapter-training registries

| `-net` | Exact registry keys | Default alias | Builder family and checkpoint expectation |
|---|---|---|---|
| `sam` | `default`, `vit_b`, `vit_h`, `vit_l` | `default` → `vit_b` | Original SAM ViT builders. They use a ViT patch size of 16, derive the embedding grid from `-image_size`, and accept a local checkpoint through `checkpoint=`. |
| `efficient_sam` | `default`, `vit_s`, `vit_t` | `default` → `vit_s` | EfficientSAM small/tiny builders. The construction code loads `torch.load(checkpoint)["model"]` with `strict=False`; use an EfficientSAM artifact, not a normal SAM checkpoint. |
| `mobile_sam` | `default`, `vit_h`, `vit_l`, `vit_b`, `tiny_vit`, `efficientvit_l2`, `PromptGuidedDecoder`, `sam_vit_h` | `default` → `vit_h` | The repository-qualified MobileSAMv2 registry. Entries do not all return the same shape, so only full model-shaped entries are ordinary `train.py` candidates. |

The MobileSAM names are not interchangeable:

- `default`, `vit_h`, `vit_l`, and `vit_b` build a SAM-like full model and
  load a flat checkpoint with `strict=False`.
- `tiny_vit` in the full `train.py` builder builds a SAM-like wrapper around
  the repository TinyViT and loads a flat state dictionary with `strict=False`.
  The separate `build_sam_vit_t_encoder` instead expects a dictionary with a
  `model` key; do not use that artifact shape for the full wrapper without
  checking its provenance.
- `efficientvit_l2` builds a full SAM-like wrapper around an EfficientViT
  encoder and loads a flat state dictionary with `strict=False`. Its
  `EfficientViTSamImageEncoder` path does not use the repository's Adapter,
  LoRA, or AdaLoRA block selectors; the MobileSAM guidance explicitly marks
  EfficientViT as not supporting the adapter recipe in this snapshot.
- `PromptGuidedDecoder` returns a dictionary with the source-spelled keys
  `PromtEncoder` and `MaskDecoder`; its builder is for the object-aware
  MobileSAMv2 route, not a full `train.py` network. `get_network`'s uniform
  `(args, checkpoint=...)` call is not compatible with this builder signature.
- `sam_vit_h` returns an image encoder only and loads its checkpoint with
  `strict=True`; it does not provide the `preprocess`, prompt encoder, and mask
  decoder interface expected by `function.train_sam`.

## Original SAM dimensions and loading

`default` and `vit_b` select the ViT-B dimensions; `vit_l` and `vit_h` select
larger embed dimensions/depths. The original builder creates an image encoder,
prompt encoder, and mask decoder, passing `args.multimask_output` to the
mask-decoder constructor. It converts the checkpoint argument to a `Path`,
may offer an interactive download for a missing checkpoint with certain
standard filenames, then keeps only keys present in the constructed model with
matching tensor shapes and loads that subset non-strictly. A partial load is
not proof that the variant is correct. Supply an existing local file and do
not answer a download prompt in an unattended run.

The image encoder uses an input/embedding grid derived from `-image_size`,
while the source SAM positional parameters and checkpoint shapes still impose
compatibility constraints. Record the image size used to build the checkpoint.

## EfficientSAM

`default` and `vit_s` use the small builder; `vit_t` uses the tiny builder.
Both use a patch size of 16 and receive `args.sam_ckpt`. The checkpoint loader
expects a top-level `model` mapping and uses non-strict loading. The loop uses
EfficientSAM's normalized point interface and always calls its mask decoder
with `multimask_output=False`, even if the shared integer flag is greater than
one. A SAM ViT-B checkpoint is not an EfficientSAM checkpoint.

EfficientSAM's encoder does select `AdapterBlock`, `LoraBlock`, or
`AdaloraBlock` for the three documented modes. Whether a supplied artifact
contains the matching parameters must still be checked before a long run.

## MobileSAM and the separate inference parser

The training utility imports `models.MobileSAMv2.mobilesamv2`, not a top-level
`mobilesamv2` package. The package registry keys are the eight names in the
matrix above. In the training loop MobileSAM receives SAM-like point prompts
and always requests one mask (`multimask_output=False`). Its ViT image encoder
selects `AdapterBlock` only for `sam_adpt` and falls back to the ordinary
`Block` for other mode strings; TinyViT has its own mode selection. Therefore
`sam_lora`/`sam_adalora` with a MobileSAM ViT entry may produce no LoRA
parameters, while MobileSAM TinyViT has a different implementation path.
Verify trainable names rather than inferring them from `-mod` alone.

The guidance notebook broadly presents MobileSAM, TinyViT, and EfficientViT
as encoder choices, but the source implementation has the compatibility
boundary above. The standalone `models/MobileSAMv2/Inference.py` parser
advertises these encoder strings:

```text
tiny_vit, sam_vit_h, mobile_sam, efficientvit_l2, efficientvit_l1, efficientvit_l0
```

Its source weight mapping implements only `tiny_vit`, `sam_vit_h`, and
`efficientvit_l2`. That parser is for object-aware box inference and is not the
same registry contract as `train.py`; route it to
[mobile inference](../../mobile-inference/SKILL.md).

## Compatibility gate

Before launching, record all of the following:

1. `-net` and exact registry key;
2. whether the artifact is a flat base model, an EfficientSAM `model` wrapper,
   a TinyViT encoder wrapper, a decoder-only dictionary, or a training wrapper;
3. `-image_size` and `-multimask_output` used to construct the model;
4. `-mod`, because it changes image-encoder block classes for some families;
5. whether the output has the full `preprocess`/image-encoder/prompt-decoder
   interface; and
6. the CUDA device and available memory.

For a training checkpoint, read [checkpoint and resume behavior](workflows.md)
and route independent loading/schema questions to
[evaluation](../../evaluation/SKILL.md).