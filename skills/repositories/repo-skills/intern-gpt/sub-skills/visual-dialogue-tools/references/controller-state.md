# Controller State

This reference explains how the visual dialogue controller keeps track of the active image, the clicked mask, the chat history, and the recovered file paths.

## Core session objects

- `state`: the visible chat transcript used by the UI.
- `user_state[0]`: the mutable session cache used by the controller.
- `user_state[0]['agent']`: the LangChain agent.
- `user_state[0]['memory']`: the conversation memory buffer.
- `user_state[0]['image_path']`: the current uploaded image copy.
- `user_state[0]['ocr_res']`: the cached full-image OCR detections.
- `user_state[0]['image_caption']`: the cached image caption.
- `user_state[0]['features']`: the cached SAM image embedding for the current image.
- `user_state[0]['seg_mask']`: the accumulated clicked segmentation mask.
- `user_state[0]['audio_path']`, `user_state[0]['video_path']`, `user_state[0]['video_caption']`: other media caches that share the same session container.
- `user_state[0]['StyleGAN']`: the DragGAN/StyleGAN state bucket; it is separate from the image-mask workflow but lives in the same session object.

## Startup and tool registration

1. `init_agent` creates a zero-temperature OpenAI-backed conversational agent with a `ConversationBufferMemory` buffer.
2. Every loaded model instance contributes each method whose name starts with `inference`.
3. The prompt-decorated method name becomes the LangChain tool name, while the prompt-decorated description becomes the tool help text.
4. Template models are assembled only when their dependency classes are already loaded in the session.

## Upload flow

### Image upload

1. `upload_image` clears per-image caches but keeps the running conversation memory.
2. `process_image` saves the uploaded image under `image/` using the generated naming scheme.
3. If Husky captioning is available, the image is captioned immediately.
4. If EasyOCR is available, the raw OCR detections are cached immediately.
5. `put_image_info_into_memory` injects a memory note that includes the image path, optional caption, optional OCR text, and a reminder to use tools instead of guessing.
6. The controller replies with `Received` and records the uploaded image path in the visible chat state.

### Save and reuse a drawn mask

- `process_save` persists the current drawn mask under `image/<...>_rawmask.png`.
- This is the escape hatch when the user has a drawn region but wants a stable mask file for later text commands.
- The saved mask path is also written into memory and echoed in the chat transcript.

## Click-mask flow

### Pick / segmentation

1. `process_seg` requires a valid uploaded image and a non-empty sketch mask.
2. If the SAM tool is not loaded, the controller returns a load reminder.
3. The first time a non-empty mask is processed, the controller caches the SAM image embedding in `user_state[0]['features']`.
4. The click mask is converted into a SAM prompt, and the resulting mask is merged with any prior selection stored in `user_state[0]['seg_mask']`.
5. The blended preview is returned to the UI, and the persistent mask is saved under `image/<...>_mask.png`.
6. The saved mask path is added to memory so later text prompts can reuse it.

### OCR on a clicked region

1. `process_ocr` requires a valid uploaded image and a non-empty click mask.
2. If OCR is not loaded, the controller records that the OCR tool is unavailable.
3. The full-image OCR detections cached during upload are filtered by the clicked mask.
4. If no characters overlap the region, the controller says no characters were found at that location.
5. Otherwise the OCR text is appended to memory and echoed in the transcript.

## Text routing

### `run_text`

1. Trim the prompt and clear temporary CUDA cache bookkeeping.
2. If the text is empty, return a prompt asking for input.
3. Download and inline any image URLs found in the text before routing.
4. Trim the agent memory to the most recent dialogue.
5. Try `exec_simple_action` first for direct remove/replace prompts.
6. If no direct action applies, call the LangChain agent.
7. If the first attempt fails, try `rectify_action` to recover tool inputs from the current message and history.
8. Extract the latest valid `image/*.png` or `image/*.mp4` path from the response and append it to the chat transcript when available.

### `exec_simple_action`

- `remove` or `erase` routes to the inpainting tool.
- `replace` routes to the masked-object replacement tool.
- The controller recovers the mask path from the current message or memory and then recovers the parent image path from the mask filename or adjacent history.
- If the mask path is missing, the controller stops early with a mask-specific reminder.
- If the image path is missing for replacement, the controller stops early with an image-specific reminder.

### `rectify_action`

- `extract` or `save` routes to the masked-extraction tool.
- `generate` or `beautify` routes to the image-to-image segmentation generator.
- `describe` or `introduce` routes to Husky captioning or masked Husky VQA, depending on whether the prompt mentions a mask.
- `image`, `figure`, or `picture` routes to full-image Husky VQA.
- If no image tool fits, the controller falls back to a plain chat response that uses memory only.

## Path recovery helpers

### `find_param`

- Scans the current message plus history for `image/<name>.png` or `image/<name>.mp4` paths.
- The `mask` keyword narrows the search to mask-like names.
- The `excluded=True` mode returns non-mask paths when the controller needs the parent image instead of the derived mask.
- When multiple candidates exist, the newest one wins.

### `find_parent`

- Uses the derived filename stem to recover the immediate parent anchor.
- Searches the current history first, then the current directory, for a sibling file that begins with that anchor.
- This only works when the file was created by the standard generated naming scheme.

## Filename conventions

- Uploaded images are copied into `image/` with a generated prefix and an `_image` suffix.
- Derived masks preserve the parent anchor in the next generated filename, so the parent image can be recovered later.
- `process_seg` saves `image/<...>_mask.png`.
- `process_save` saves `image/<...>_rawmask.png`.
- Generated edits and control-image outputs generally save under `image/<...>_<ToolName>.png`.

## Memory behavior

- `clear_user_state(False, user_state)` resets per-media state while preserving conversation memory.
- The clear button uses `clear_user_state(True, user_state)` to reset the conversation memory too.
- `e_mode` shifts several models onto GPU only for a call and then back to CPU, so repeated calls may repopulate state from memory rather than from device residency.
