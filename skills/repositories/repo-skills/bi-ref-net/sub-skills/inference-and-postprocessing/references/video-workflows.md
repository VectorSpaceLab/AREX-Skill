# BiRefNet Video Inference Workflows

## Notebook workflow summary

- Find video files with `.mp4` or `.avi`.
- Derive a model name from the hub checkpoint name.
- Open each video with OpenCV, read its FPS, and extract frames into a per-video folder such as `frames-<model>-video_<stem>/frame_<index>.png`.
- Reuse the same preprocessing as image inference: RGB conversion, `Resize(config.size)`, `ToTensor`, ImageNet normalization.
- Batch frames through `birefnet(input)[-1].sigmoid()`.
- Resize each predicted mask back to the frame size.
- Save two outputs with `VideoWriter_fourcc(*'mp4v')`:
  - `-preds_mask-<model>.mp4` with `isColor=False`
  - `-preds_subject-<model>.mp4` with `isColor=True`
- Preserve the original video FPS when writing.

## Foreground / matting preview

- Use `refine_foreground(image, mask, device='cuda' or 'cpu')` on each frame when you want subject extraction instead of a plain mask.
- Attach the prediction mask as alpha and composite the subject on a solid background for a preview video.
- If the mask and frame sizes disagree, the refinement helper resizes the mask to the frame size.

## Operational guidance

- Keep the batch size small unless you have plenty of memory.
- Release both `VideoWriter` objects explicitly after processing each video.
- If the writer produces an empty or corrupt file, check:
  - the source FPS is non-zero
  - the codec backend supports `mp4v`
  - the input file extension is one of the supported video types
- If the output container is not available on the local system, export frames only and transcode later with a different tool.
- For long clips, keep frame extraction and inference separate so failures do not require rereading the source video.

## When to route away

- Codec conversion, ffmpeg-specific workarounds, and export engineering belong in broader deployment or postprocessing notes, not in the core image inference helper.
- The bundled runtime CLI is image-focused; use the video notebook recipe or a custom wrapper when you need full video export.
