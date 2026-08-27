# Video tool reference

## Shared behavior

- Video uploads are copied into a renamed local file and the new path is stored in conversation state.
- When the caption tool is available, upload-time pre-captioning adds a richer note to memory; otherwise the upload falls back to a generic video description.
- The runtime video loader caches the most recent clip path, so repeated calls on the same file are cheaper than the first decode.
- Timeline text in this family of tools is sample-index based. It uses `Second N` labels for readability, but the counts come from decoded frame positions rather than a true clock.

## Tool contracts

### `ConversationBot.upload_video`
- **Input:** one local video path.
- **Output:** a renamed copy of the uploaded clip, plus a state update that records the path and a short confirmation message.
- **Behavior:** the upload is preserved as a real file path for later tool calls. If video captioning is available, the upload step also stores a pre-caption in memory.
- **Use when:** the user has just uploaded a clip and wants the assistant to remember it before asking follow-up questions.

### `VideoCaption`
- **Input:** one local video path as a plain string.
- **Output:** a list of caption strings and a cached tag list.
- **Role:** Tag2Text-style captioning for the clip as a whole.
- **Framewise details:** `framewise_details` groups repeated caption runs and emits lines in the form `Second <start> - <end>: <caption><frame-index>`, then ends with `| Total Duration: <N> seconds.`
- **Use when:** the user says "caption this video", wants tags, or needs a rough timeline summary.

### `ActionRecognition`
- **Input:** one local video path as a plain string.
- **Output:** one Kinetics class label string.
- **Role:** InternVideo-style action recognition over a small sample of frames.
- **Sampling pattern:** the runtime samples 8 frames from the clip before classification.
- **Use when:** the user wants the dominant action class, not a long caption.

### `DenseCaption`
- **Input:** one local video path as a plain string.
- **Output:** timestamped dense descriptions built from sampled frames.
- **Role:** GRiT-style dense captioning over the clip.
- **Sampling pattern:** the runtime samples every 5th frame and reports the detected object names for each sampled position.
- **Use when:** the user wants dense visual detail, object lists, or per-frame scene cues.

### `GenerateTikTokVideo`
- **Input:** a comma-separated pair of `video_path, prompt`.
- **Output:** a tuple containing the final short-form mp4 path.
- **Role:** a composite workflow that chains action recognition, captioning, dense captioning, timestamp selection, narration generation, clipping, and audio muxing.
- **Internal sequence:**
  1. Read the action label, caption list, tags, framewise summary, and dense descriptions.
  2. Ask the language model for a start/end range that matches the user prompt.
  3. Generate narration text.
  4. Synthesize audio.
  5. Trim or loop the source clip with ffmpeg so the video length matches the narration.
- **Use when:** the user asks for a TikTok-style cut, a highlight clip, or a narrated short-form edit.

## Expected artifacts

- Uploaded-video copies are renamed local video files for later tool calls.
- Captioning yields a caption list, tag cache, and a framewise summary string.
- Action recognition yields a single class label.
- Dense captioning yields a timestamped object-name report.
- TikTok generation normally produces:
  - one final mp4 clip,
  - one temporary clipped mp4,
  - one generated wav narration file,
  - and, when looping is needed, a temporary concat manifest.

## Required prerequisites

- **Tag2Text:** needed for `VideoCaption` and therefore for `GenerateTikTokVideo`.
- **uniformerv2:** needed for `ActionRecognition` and therefore for `GenerateTikTokVideo`.
- **detectron2 + GRiT weights:** needed for `DenseCaption` and therefore for `GenerateTikTokVideo`.
- **ffmpeg:** needed for probing, clipping, and muxing the TikTok output.
- **Bark:** needed for narration audio generation.
- **OpenAI key:** needed for timestamp selection and narration polishing in the TikTok flow.

## Output discipline

- Treat `GenerateTikTokVideo` as a composite flow, not a standalone primitive.
- Do not promise a final mp4 if any prerequisite in the chain is missing.
- Prefer the smallest valid workflow that satisfies the user request.
