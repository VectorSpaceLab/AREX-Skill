# Training troubleshooting

Use this order: check parser values and the static tuple, check input artifact
roles and shapes, check CUDA/dependencies, then check memory and outputs. Keep
the exact command, effective boolean values, `-net`/`-encoder`/`-mod`, image and
chunk settings, checkpoint provenance, device mapping, and output paths with
every failure.

## Checkpoint and variant failures

| Symptom | Likely source cause | Recovery |
|---|---|---|
| `-sam_ckpt` is omitted, `Path(None)`/`FileNotFoundError`, or a download prompt appears | The selected builder needs a base checkpoint. Original SAM may offer an interactive download for certain standard filenames. | Stop the unattended run. Supply an existing local checkpoint, verify its family/encoder, and do not download implicitly. |
| Many missing/unexpected keys or shape mismatches | SAM, EfficientSAM, MobileSAM, encoder, image size, or mode-specific blocks do not match the artifact. Non-strict loading can conceal this. | Re-run the static registry check, inspect the artifact's wrapper shape and provenance, and restore the matching `-net`, `-encoder`, `-mod`, and `-image_size`. Compare key/shape coverage before GPU work. |
| EfficientSAM says `model` is missing | Its builder loads `torch.load(checkpoint)["model"]`; a flat SAM/MobileSAM state dict was supplied. | Use an EfficientSAM artifact with the expected top-level mapping. Do not rename keys blindly. |
| MobileSAM TinyViT says `model` is missing, or a full wrapper rejects a `model` mapping | The standalone TinyViT encoder builder expects `state_dict['model']`, while the full `tiny_vit` wrapper builder loads the flat state dict. | Match the checkpoint to the exact constructor; the registry name alone is insufficient. |
| `PromptGuidedDecoder` has no full model interface or raises a call-signature error | It returns `{'PromtEncoder': ..., 'MaskDecoder': ...}` and its builder is for object-aware inference, while `get_network` uses a uniform full-model call. | Do not use it as a `train.py` network. Route to [mobile inference](../../mobile-inference/SKILL.md). |
| `sam_vit_h` lacks `preprocess`, prompt encoder, or mask decoder | The registry entry returns an image encoder only and loads strictly. | Use a full MobileSAM model entry for adapter training or route the encoder-only artifact to its intended workflow. |
| `-weights` fails on missing `epoch`, `best_tol`, `state_dict`, or `path_helper` | A raw base checkpoint, partial LoRA state dict, or unrelated evaluator checkpoint was passed as a training wrapper. | Use a wrapper emitted by this training path. Put the raw base model in `-sam_ckpt`; route independent checkpoint diagnostics to evaluation. |
| Checkpoint loads with `strict=False` but the run has no useful trainable parameters | Partial loading hid an incompatible architecture or a mode created ordinary blocks instead of LoRA/AdaLoRA blocks. | Inspect trainable names and tensor shapes. Do not treat non-strict loading as compatibility proof. |

## Mode and parameter failures

- With `sam_adpt`, inspect image-encoder names containing `Adapter`. If none
  are trainable, construction did not use the adapter block or the wrong
  network path was selected.
- With `sam_lora`, inspect `lora_A`/`lora_B` names and `requires_grad` before a
  long run. `mark_only_lora_as_trainable` freezes image-encoder parameters
  without `lora_` in their name.
- With `sam_adalora`, the loop expects LoRA/SVD parameters and a rank allocator.
  Original SAM's image encoder and SAM-like MobileSAM ViT paths construct the
  ordinary block for this mode in this snapshot. EfficientSAM and TinyViT have
  a dedicated AdaLoRA block. A missing parameter is a source compatibility
  blocker; do not silently switch modes.
- The fallback for any other mode makes every image-encoder parameter
  trainable. Its memory and checkpoint behavior are not a documented
  lightweight recipe.
- The mode branch does not explicitly freeze prompt/decoder modules. The
  prompt encoder call is under `no_grad`, while the decoder may remain in the
  optimizer. Confirm actual gradient counts if this distinction matters.

## OOM and memory controls

### 2D

1. Lower `-b` first.
2. Lower `-image_size`, then keep `-out_size` and the label contract coherent.
3. Increase `-vis` to reduce visualization frequency.

Changing `-image_size` changes the model embedding grid and can invalidate a
checkpoint's shapes. Do not use OOM tuning to change `-mod`, classes, prompt
labels, or channel semantics.

### 3D

The MONAI crop is `(roi_size, roi_size, chunk)` and `num_sample` controls how
many positive/negative crops are created per source volume. Lower `-b`, then
`-chunk`, `-num_sample`, and `-roi_size` as needed. Validation is separate:
lower `-evl_chunk` without silently changing training `-chunk`. The source
validation loop advances only complete windows and can skip a depth remainder;
choose a divisor where possible and record the limitation. Keep `-thd` truthy
for 3D. Data-loader caching and device-side MONAI transforms can retain memory;
change those only through a verified custom loader, not by changing labels.

## Resume and output failures

- The expected `-weights` object is a wrapper with `epoch`, `model`,
  `state_dict`, `optimizer`, `best_tol`, and `path_helper` fields. The loader
  actually reads only `epoch`, `best_tol`, `state_dict`, and `path_helper`.
- Optimizer loading is commented out. A resumed run is a warm start, not an
  exact continuation of optimizer state or scheduler state.
- The source loads the old `path_helper` and then immediately calls
  `set_log_dir('logs', args.exp_name)`, so it creates a new timestamped
  `logs/<exp_name>_<timestamp>/Model`, `Log`, and `Samples` tree. Use a new
  experiment name and preserve the command manifest.
- The source creates a global `checkpoint/<net>/<TIME_NOW>` directory, but the
  shown save call writes the best files under the experiment `Model` directory.
  Look there before declaring a checkpoint missing.
- Do not delete a partially created output tree until checking whether its
  `best_dice_checkpoint.pth` or `checkpoint_best.pth` is readable. A raw
  `state_dict` alone is not the wrapper expected by `-weights`.
- The saved `best_tol` field is populated from `best_dice` in the source, not
  the variable named `best_tol`; preserve this source quirk in diagnostics.

## Data handoff failures

- An unknown dataset key is a dispatcher problem. Use the case-sensitive table
  and layouts in [data preparation](../../data-preparation/references/dataset-layouts.md).
- A custom sample must provide `image` and `label`; prompts may be supplied as
  `pt` with coherent `p_label`, otherwise the loop generates click prompts.
  `image_meta_dict['filename_or_obj']` is needed by visualization/log naming.
- 2D samples are `[C,H,W]`; 3D samples are `[C,H,W,D]` with matching image and
  label depth. Do not flatten a volume in a custom loader and also enable
  `-thd` unless that adapter explicitly expects it.
- `-multimask_output 2` does not turn a one-channel mask into two classes. Use
  the REFUGE two-channel cup/disc contract and the exact uppercase training
  key. The source's REFUGE best-checkpoint branch also references an undefined
  `edice` variable after unpacking cup/disc metrics; record this as a source
  bug rather than hiding it as a layout issue.
- `decathlon` needs MONAI transforms, imaging/NIfTI support, and a valid
  `dataset_0.json`. Missing files or packages belong to data preparation, not
  model-variant recovery.

## CUDA and optional dependencies

- `function.py` initializes CUDA state and AMP at import; the training loop
  creates `cuda:<gpu_device>` tensors. CPU-only execution is unsupported even
  if `-gpu False` is supplied.
- `CUDA_VISIBLE_DEVICES` remaps visible indices. If it exposes one physical
  device as visible index 0, pass `-gpu_device 0`, not the original host ID.
  Verify availability, device name, and a small allocation before launch.
- `-distributed 0,1` uses `DataParallel` and requires all listed devices. Start
  with one visible device and only add distributed operation after a working
  single-device smoke.
- The selected dataset may require PIL, scikit-image, OpenCV, nibabel,
  SimpleITK, MONAI, tensorboardX, einops, or other optional packages. Install
  only what the selected route needs and run a dependency/import preflight;
  do not install the contradictory legacy environment specification blindly.
- Standalone MobileSAMv2 object-aware inference adds detector and weight
  requirements and has a hard CUDA box-tensor operation. It is not a CPU
  fallback for adapter training; route its failures to
  [mobile inference](../../mobile-inference/SKILL.md).

## Parser and validation traps

- Omit `-thd` for 2D. `-thd False` is truthy.
- Do not use `-gpu False` to claim CPU support.
- Pass a positive `-vis`; `None` can fail in validation.
- `-pretrain` is declared `bool` but used as a checkpoint path when truthy,
  so treat it as an unresolved legacy option rather than a path interface.
- Keep `-val_freq` positive. The loop validates before training in the first
  five zero-based epochs and on the final epoch regardless of interval.

For independent state-dict loading, metric interpretation, and visualization,
route to [evaluation](../../evaluation/SKILL.md). For file/layout and
checkpoint-environment repair, route to [data preparation](../../data-preparation/SKILL.md).
For shared root routing, use the [root skill](../../../SKILL.md) and its shared
troubleshooting when present.
