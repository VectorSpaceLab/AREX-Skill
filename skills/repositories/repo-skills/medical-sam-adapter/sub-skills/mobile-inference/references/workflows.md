# Workflow mechanics

## Preflight before any model import

Use the bundled helper first. It validates all local inputs and reports every
failure without importing model code or writing output:

```bash
python scripts/run_mobile_samv2.py --help
python scripts/run_mobile_samv2.py \
  --ObjectAwareModel_path /weights/ObjectAwareModel.pt \
  --Prompt_guided_Mask_Decoder_path /weights/Prompt_guided_Mask_Decoder.pt \
  --encoder_path /weights/mobile_sam.pt \
  --encoder_type tiny_vit \
  --img_path /images \
  --output_dir /results \
  --dry-run
```

Keep `/results` distinct from `/images`; the helper checks supported image
extensions and existing output names. It does not inspect checkpoint tensor
schemas and does not run inference.

## Source-equivalent inference flow

A separately maintained real runner should preserve this sequence on a CUDA
host:

1. Construct the detector from the explicit ObjectAwareModel checkpoint and
   construct the prompt-guided decoder from its explicit checkpoint. Build the
   SAM shell with the prompt encoder and mask decoder returned by the
   `PromptGuidedDecoder` registry entry.
2. Build the selected image encoder from the explicit `encoder_path` using the
   operational mapping in [the CLI reference](cli-reference.md), attach it to
   the SAM shell, move the model and detector to CUDA, and set evaluation mode.
3. Enumerate the supplied image **directory**. For each supported image, read
   with OpenCV, then convert BGR to RGB before both detector and predictor use.
   Reject unreadable images; do not pass a missing path or `None` to the
   detector.
4. Call the detector with the RGB array and the source-equivalent controls:
   `retina_masks`, `imgsz`, `conf`, and `iou`. Read boxes from
   `results[0].boxes.xyxy`. An empty result should be handled as “no objects”
   rather than indexed blindly.
5. Call the SAM predictor's box transform with the original image size. The
   source transforms NumPy XYXY boxes to the resized SAM frame, converts them
   to a torch tensor, and places that tensor on CUDA.
6. Compute one image embedding and dense positional encoding. Repeat the
   embedding/positional encoding to match the prompt batch and process boxes
   in batches of **320**. For each batch, invoke the prompt encoder with
   `points=None`, `boxes=batch_boxes`, and `masks=None`, then call the mask
   decoder with `multimask_output=False` and source-specific `simple_type=True`.
7. Postprocess masks back to the original image size and threshold using the
   model mask threshold. Concatenate mask batches. The source sorts masks by
   descending pixel area before rendering.
8. Render a white background, overlay random-color masks, hide axes, and save
   one rendered image under the explicit output directory using the input
   filename. Prefer collision checks and deterministic naming in a maintained
   runner; the original rendering uses Matplotlib and may overwrite a file.

This sequence is a behavioral guide, not an invitation to execute the source
script from a checkout. The supplied source had inconsistent parsed versus
hard-coded paths, and the optional detector import was not executed. Resolve
those issues in the maintained runner and retain the no-download contract.

## Thresholds and batching

The source defaults are `imgsz=1024`, `iou=0.9`, `conf=0.4`, and `retina=True`.
The box batch size is hard-coded to 320, independent of detector batch size.
Lowering it is a memory-oriented implementation change, not an exact source
reproduction; if changed, document the value and expected memory effect. The
source repeats image features for 320 and slices the final batch, so a runner
must ensure feature and prompt tensors are sliced consistently.

## Scope links

Adapter training and its encoder/adaptation variants belong to
[training](../../training/). Dataset layout and image/sample contracts belong
to [data preparation](../../data-preparation/). This route owns only the
standalone object-aware inference path.
