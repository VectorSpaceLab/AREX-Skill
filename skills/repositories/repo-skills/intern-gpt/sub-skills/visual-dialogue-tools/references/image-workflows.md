# Image Workflows

Use these recipes when the user is interacting with one image at a time and wants region-aware dialogue, OCR, inpainting, or control-image generation.

## 1. Upload and ask about the image

1. Upload the image through the controller.
2. The image is copied into `image/` and the session memory is primed with a caption and any OCR text that was available.
3. Ask a general scene question such as what is present, what the background is, or how many objects are visible.
4. The controller routes the question to HuskyVQA when the prompt is about visual semantics rather than exact text.

## 2. Pick a region and get a segmentation mask

1. Draw or click a region in the sketch widget.
2. Press Pick.
3. If the mask is non-empty, the controller caches the SAM embedding and writes a persistent mask file under `image/`.
4. Use the saved mask path later if the conversation loses track of the selection.

## 3. OCR versus Husky on a selected region

- Use OCR when you need the literal characters inside the clicked region.
- Use Husky masked VQA when you need a description, object identity, color, count, or other visual meaning inside the clicked region.
- If the user asks both, answer the exact text first and the scene semantics second.

## 4. Remove or replace a selected object

### Remove

1. Make sure the current image and mask are both available.
2. Recover the parent image from the mask path if the user only remembers the mask.
3. Route to the inpainting removal tool.
4. Expect a new PNG under `image/`.

### Replace

1. Keep the same image and mask pair.
2. Add the replacement prompt in the third field after the second comma.
3. Route to the masked-object replacement tool.
4. Expect a new PNG under `image/`.

## 5. Save a scribble or raw mask for later reuse

1. Draw the mask or scribble in the widget.
2. Press Save.
3. The controller stores a persistent `image/<...>_rawmask.png` file.
4. Use that file later for removal, replacement, or extraction-style prompts.

## 6. Extract the masked object instead of editing it

- Use the extraction path when the user wants to keep only the selected pixels.
- This is useful when the request says save, extract, keep, crop, or isolate the masked region.
- The output is an RGBA PNG that can preserve transparency around the selected object.

## 7. Generate from control maps

- Use `Beautify The Image` when you want the controller to segment the image and then generate a refined image from the segmentation.
- Use `Image2Canny` then `CannyText2Image` when the user wants an edge-conditioned generation.
- Use `Image2Scribble` then `ScribbleText2Image` for sketch-conditioned generation.
- Use `Image2Depth` then `DepthText2Image` for depth-conditioned generation.
- Use `Image2Normal` then `NormalText2Image` for normal-map-conditioned generation.
- Use the pose, line, and HED pairs in the same way when those control maps are the right abstraction.

## 8. Image path recovery when only a mask remains

1. Use the filename anchor rule or the safe validator with parent checking.
2. Look for the immediate source image that shares the same generated anchor.
3. If the image cannot be recovered, re-upload the source image rather than guessing the path.
4. Do not ask a removal or replacement tool to operate on a mask without a known parent image.

## 9. Text inside selection versus visual semantics inside selection

- If the user asks for the words on a sign, button, label, or document region, choose OCR.
- If the user asks what the sign, button, or region means visually, choose Husky masked VQA.
- If the user asks to delete the region, choose removal.
- If the user asks to transform it into a different object, choose replacement.

## 10. Prompt grammar cheatsheet

- `image_path` only: full-image captioning, full-image VQA, preprocessing maps.
- `image_path,mask_path`: clicked segmentation, extraction, removal, OCR by mask, masked Husky VQA.
- `image_path,mask_path,prompt`: replacement.
- `image_path,prompt`: control-map generators and beautify workflows.
- `text`: plain text-to-image.

## 11. Expected output naming

- Uploaded images end in `_image.png`.
- Derived masks end in `_mask.png`.
- Raw saved masks end in `_rawmask.png`.
- Control-map and edit outputs usually end in `_<ToolName>.png`.
- If the user asks for a file path, quote the generated `image/` path exactly and avoid inventing a new one.
