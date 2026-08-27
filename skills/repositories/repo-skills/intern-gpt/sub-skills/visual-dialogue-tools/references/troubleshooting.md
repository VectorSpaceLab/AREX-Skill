# Troubleshooting

Use this guide when a visual workflow fails, a mask cannot be reused, a checkpoint is missing, or the prompt grammar is unclear.

## Unloaded tool

**Symptom:** The controller says the segmentation, OCR, Husky, inpainting, or replacement tool is not loaded.

**Likely cause:** The running service did not load that model class.

**Fix:** Route the issue to the deployment sub-skill or reload the service with the missing tool class enabled. This sub-skill only explains the visual workflow once the tool exists.

## Empty mask or no selection

**Symptom:** Pick or OCR says to click the image, or Save says the mask cannot be found.

**Likely cause:** The sketch mask is empty.

**Fix:** Draw a non-empty region, then press the button again. For a reusable file, press Save so the mask is written to `image/<...>_rawmask.png`.

## Wrong path order

**Symptom:** Removal, replacement, OCR, or Husky returns a path error or a nonsense answer.

**Likely cause:** The image and mask arguments were swapped, or the prompt text was inserted in the wrong slot.

**Fix:** Recheck the grammar:

- `image_path,mask_path`
- `image_path,mask_path,prompt`
- `image_path,question`
- `image_path,prompt`

If the prompt itself contains commas, use the exact grammar from the reference table rather than guessing.

## Parent image recovery

**Symptom:** The user only has a mask path in memory, and removal or replacement no longer knows which source image to use.

**Likely cause:** The parent image was not re-derived from the filename anchor.

**Fix:** Recover the parent through the generated filename convention or re-upload the original image. The safe validator can help confirm whether a mask path and its intended parent match.

## Missing checkpoints

### SAM

- Expected file: `model_zoo/sam_vit_h_4b8939.pth`
- If missing, segmentation cannot run.

### Husky

- Expected result: a converted Husky checkpoint directory built from the LLaMA base plus the delta files.
- If the base LLaMA files are missing or partially downloaded, delete the broken partial directory and rebuild cleanly.
- If the converted folder is missing metadata such as `config.json`, it is usually a sign of an incomplete or interrupted setup.

### LaMa / inpainting / removal

- Expected file for the controller's removal tool: `model_zoo/ldm_inpainting_big.ckpt`
- Historical LaMa-style materials may mention a separate `big-lama` model directory; treat that as a different inpainting asset unless the running service explicitly uses it.
- If the required inpainting asset is missing, the removal path cannot run.

### Stable Diffusion / ControlNet

- These models are usually fetched from Hugging Face on first use.
- If the first call fails, the issue is often network, cache, or missing dependency related rather than a bad prompt.

### EasyOCR

- The reader uses Chinese and English OCR assets.
- If OCR returns nothing, the mask may not cover text or the scene may have no detectable characters.

## EasyOCR returns no text

**Symptom:** OCR on a clicked region says no characters were found.

**Likely cause:** The mask is too loose, too small, or not over the text.

**Fix:** Tighten the click region, choose a higher-contrast crop, or try full-image OCR first. If the object is visual rather than textual, switch to Husky masked VQA.

## e-mode memory behavior

**Symptom:** A later call is slower or seems to reload weights.

**Likely cause:** The model is intentionally moved back to CPU between calls.

**Fix:** Treat e-mode as memory-saving, not residency-preserving. It reduces GPU pressure by moving several models onto GPU only for the active call.

## Comma grammar mistakes

**Symptom:** A prompt that should have worked is truncated or parsed as the wrong argument list.

**Likely cause:** The tool parser split the string at the wrong comma.

**Fix:**

- Put the path in the first slot.
- Put the mask in the second slot when a mask is expected.
- Put the prompt last.
- For tool classes that only consume the first comma-separated prompt fragment, avoid commas in the prompt text.

## When to stop and reroute

- If the problem is about startup flags, certificates, or which tools are loaded into the service, use the deployment sub-skill.
- If the problem is about audio, thermal, or DragGAN point editing, use the cross-modal-generation sub-skill.
- If the problem is about video understanding or generated clips, use the video-understanding sub-skill.
