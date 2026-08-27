# Shared troubleshooting

Use the route-specific troubleshooting file first, then apply this boundary
check. Do not paper over a failure by changing model family, labels, or paths
until the failing contract is identified.

## Environment and imports

1. Use an isolated environment with a binary CUDA-enabled PyTorch/torchvision
   pair appropriate for the host. Confirm `torch.cuda.is_available()`, the
   selected device name/capability, and a one-element CUDA allocation.
2. Treat `environment.yml` as historical evidence, not a blind installation
   command: its CPU-only pin conflicts with its CUDA pip entries and it contains
   unrelated breadth.
3. Import failures are not interchangeable. Missing MONAI/NIfTI/OpenCV/
   tensorboardX dependencies affect different routes. Install only the missing
   dependency in the user-selected environment, then rerun a bounded import
   check. Do not copy vendored detector or EfficientViT trees into this skill.
4. Keep the repository-qualified MobileSAMv2 package layout in mind. A
   top-level `mobilesamv2` import is invalid for this source's relative imports;
   the documented source layout is repository-qualified. The prompt-guided
   detector path has an additional compatible Ultralytics dependency boundary.
5. If a CUDA device is busy, select a user-authorized visible device explicitly;
   do not claim that CPU execution verifies training, evaluation, or standalone
   inference.

## Configuration and command misuse

- The shared parser uses one-dash flags such as `-net`, `-encoder`, `-mod`,
  `-sam_ckpt`, `-weights`, `-dataset`, and `-data_path`. Use the exact spellings
  in the route CLI references.
- Several booleans use `type=bool`; `-thd False` and similar strings may parse as
  true. Prefer the parser's effective value or a reviewed wrapper rather than
  assuming conventional flag semantics.
- `-sam_ckpt` is a base model artifact used while constructing the network;
  `-weights` is the saved experiment wrapper expected by independent evaluation.
  They are not interchangeable.
- Check exact, case-sensitive registry/dataset names before a run. Unknown
  values should fail during preflight, not after a data loader or model has been
  constructed.
- Keep the selected `-image_size`, encoder, checkpoint family, and output class
  count coherent. A permissive `strict=False` load can otherwise accept an
  almost-empty or wrong-shaped state dict.

## Data and prompt contract

- A 2D sample is `[C,H,W]`; a 3D sample is `[C,H,W,D]`. Image and label ranks
  and depth must agree. The bundled sample validator checks metadata and prompt
  bounds but cannot decode NIfTI, prove dtype semantics, or run MONAI transforms.
- Dataset adapter names are not website names. Confirm required CSVs, split JSON,
  image/label pairing, and the adapter-specific channel count in
  [data-preparation](../sub-skills/data-preparation/SKILL.md).
- The source has a broken/unfinished `LIDC` dispatch (`MyLIDC` is not provided by
  the inspected registered module). Treat it as blocked until separately fixed
  and verified; do not silently substitute another adapter.
- REFUGE is a two-mask/cup-disc case in the documented route. Do not collapse
  its channel metrics into one foreground score without recording the change.
- If a 3D prompt or mask has an inconsistent depth, stop before loader creation.
  For MONAI Decathlon/BTCV, verify `imagesTr`, `labelsTr`, and the split JSON as
  well as the preprocessed spatial/chunk assumptions.

## Model, checkpoint, and adaptation failures

- Select a complete model builder for `train.py`. `PromptGuidedDecoder` and
  `sam_vit_h` in the MobileSAM registry are components/encoders, not ordinary
  complete training networks; route them to standalone MobileSAMv2 when that is
  the actual goal.
- Match base checkpoints to the exact family/encoder. Original SAM, EfficientSAM,
  MobileSAM, TinyViT, EfficientViT, decoder bundles, and experiment wrappers
  have different state-dict contracts. Use the route checkpoint inspectors
  before a long CUDA job.
- Adapter/LoRA/AdaLoRA mode changes which parameter blocks are constructed and
  trainable. Inspect trainable names in a short smoke; do not infer success from
  a loss value alone. The source snapshot has family-specific limitations listed
  in [training model variants](../sub-skills/training/references/model-variants.md).
- For independent evaluation, validate the wrapper's `state_dict` and loading
  prefix before invoking `val.py`; missing `epoch`, `best_tol`, or path metadata
  may be diagnostic even when the evaluator only indexes some fields.

## Memory, CUDA, and outputs

- For 2D OOM, lower `-b` and then `-image_size`; keep checkpoint/model selection
  unchanged while diagnosing.
- For 3D OOM, lower `-b`, `-chunk`, `-num_sample`, and evaluation `-evl_chunk` in
  that order as appropriate. `-roi_size` and spatial labels must remain coherent.
  The source evaluation loop can skip a trailing depth remainder when
  `evl_chunk` is not a divisor; choose a divisor or record the limitation.
- Invalid device, `.cuda()` errors, or allocator failures are backend blockers,
  not reasons to silently switch to CPU. Capture the device selection and free
  memory in the run record.
- Use new or explicitly managed log/checkpoint/output directories. The training
  code writes under its log/checkpoint configuration; standalone inference writes
  rendered files and can overwrite names if the output path is not separated.
  Check permissions and collision policy before starting a side-effecting run.

## Escalation and verification limits

A helper returning `VALID` proves only the stated metadata or checkpoint
preflight. It does not prove real image decoding, model tensor compatibility,
CUDA execution, metric correctness on a dataset, or visual quality. Full jobs,
notebooks, downloads, and rendering remain user-authorized operations. Preserve
an unresolved required-CUDA or required-dependency blocker as a blocker rather
than reporting a partial smoke as a complete workflow success.
