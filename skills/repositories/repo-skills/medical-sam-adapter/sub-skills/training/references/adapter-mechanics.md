# Adapter, LoRA, and AdaLoRA mechanics

The `-mod` value is consumed during model construction and again inside
`function.train_sam`. Keep the same mode for construction, training, resume,
and later evaluation. The source changes only image-encoder `requires_grad`
flags in its mode branches; the prompt encoder is called under `no_grad`, while
the mask decoder is not explicitly frozen. Verify actual parameter counts for
a chosen network rather than assuming a mode freezes the complete model.

## Mode matrix by source path

| Mode | Original SAM image encoder | EfficientSAM image encoder | MobileSAM image encoder | Training-loop action |
|---|---|---|---|---|
| `sam_adpt` | `AdapterBlock` | `AdapterBlock` | `AdapterBlock` for the SAM-like ViT path; TinyViT has its own adapter block; EfficientViT does not use these selectors | Freeze image-encoder names without `Adapter`; enable names containing `Adapter`. |
| `sam_lora` | `LoraBlock` | `LoraBlock` | The SAM-like MobileSAM ViT path falls back to ordinary `Block`; TinyViT has a LoRA block; EfficientViT has no custom LoRA block | Call `mark_only_lora_as_trainable` on `net.image_encoder`; all names without `lora_` are frozen. |
| `sam_adalora` | Ordinary `Block` in this source's original SAM image encoder | `AdaloraBlock` | The SAM-like ViT path falls back to ordinary `Block`; TinyViT has an AdaLoRA block; EfficientViT has no custom AdaLoRA block | Call `mark_only_lora_as_trainable`, add orthogonal regularization, and update a `RankAllocator`. This can mismatch the constructed block. |
| Any other string | Ordinary `Block` | Ordinary `Block` | Ordinary `Block` on the SAM-like ViT path | Make every image-encoder parameter trainable. This is an undocumented full-encoder fallback, not a portable recipe. |

The network-specific columns matter. In particular, do not promise Adapter,
LoRA, or AdaLoRA parameters for MobileSAM's `efficientvit_l2` path or its
ordinary ViT entries under `sam_lora`/`sam_adalora`, and do not call
`sam_adalora` a dedicated original-SAM AdaLoRA block: the source's
`models/sam/modeling/image_encoder.py` selects ordinary `Block` for that value.
EfficientSAM and repository TinyViT do select an AdaLoRA block.

## Adapter blocks

The adapter implementations expose `MLP_Adapter`, `Space_Adapter`, and
`Depth_Adapter` submodules. `-mid_dim` sets their bottleneck width; if omitted,
the adapter width defaults to the block dimension. The training loop's string
test for `"Adapter"` therefore enables these image-encoder parameters and
freezes the other image-encoder parameters.

When `-thd` is truthy, `AdapterBlock` adds a depth interaction path. The source
reshapes 3D data into slice batches for the 2D encoder and uses `-chunk` to
recover depth grouping inside the adapter. 3D mode is not just a different file
layout; preserve the `[C,H,W,D]` contract and the chunk choices from
[data preparation](../../data-preparation/SKILL.md).

The mode branch does not explicitly set `requires_grad=False` on the prompt
encoder or mask decoder. In the shown loop the prompt encoder call is under
`torch.no_grad()`, and the decoder remains in the optimizer's parameter list;
inspect the actual `requires_grad`/gradient counts if a lightweight update is
required.

## LoRA layers

Original SAM, EfficientSAM, and the TinyViT LoRA blocks replace selected linear
operations with the repository's `models.common.loralib` layers:

- `-mid_dim` is the LoRA rank; if omitted, the block defaults to rank `4`.
- Attention uses a `MergedLinear` with LoRA enabled for the query/value slices;
  MLP layers use LoRA `Linear` layers.
- The layers retain frozen base weights and add `lora_A`/`lora_B` updates with
  scaling `lora_alpha / r`.
- `mark_only_lora_as_trainable` freezes every image-encoder parameter whose
  name does not contain `lora_`.
- The layer implementation merges the low-rank update into the base weight on
  `eval()` and unmerges on `train()` when `merge_weights` is enabled. Resume
  and evaluation with the same mode and compatible architecture.

A mode flag alone does not establish that the selected builder created LoRA
layers. Check for `lora_A`/`lora_B` names before spending GPU time.

## AdaLoRA source behavior and limitation

Inside `train_sam`, `sam_adalora` creates a `RankAllocator` with these exact
constants:

```text
lora_r=4, target_rank=8
init_warmup=500, final_warmup=1500, mask_interval=10
total_step=3000, beta1=0.85, beta2=0.85
```

The loss becomes `loss + 0.1 * compute_orth_regu(net)`. After the optimizer
step the loop calls `rankallocator.update_and_mask(net, ind)`, where `ind` is
the batch counter. This expects the constructed network to contain the
necessary SVD/LoRA parameters. Original SAM and SAM-like MobileSAM ViT paths
do not construct such a block for `sam_adalora` in this snapshot; a missing
parameter or empty trainable set is a source incompatibility, not a reason to
silently switch to `sam_lora`.

## Optimizer and output implications

The optimizer is Adam over `net.parameters()` with `lr=args.lr` (the parsed value),
betas `(0.9, 0.999)`, zero weight decay, `amsgrad=False`, and `eps=1e-8`.
A StepLR with `step_size=10` and `gamma=0.5` is constructed but the shown SAM
loop does not step it. Checkpoint state therefore contains an optimizer entry,
but the resume path does not restore that optimizer state. See
[workflows](workflows.md) for the exact wrapper schema.

For prompt/decoder interfaces and metric behavior, route to
[evaluation](../../evaluation/SKILL.md). For source-specific mode or checkpoint
failures, use [troubleshooting](troubleshooting.md) and the
[Medical SAM Adapter root skill](../../../SKILL.md).