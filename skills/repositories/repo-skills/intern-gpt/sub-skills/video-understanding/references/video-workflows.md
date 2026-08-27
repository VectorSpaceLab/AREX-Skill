# Video workflows

## Choose the smallest workflow that fits the request

| User intent | Tool plan | What to return | What not to promise |
| --- | --- | --- | --- |
| Upload or remember a clip | `ConversationBot.upload_video` | renamed local video path plus a short confirmation | captioning if the caption tool is not available |
| "Caption this video" | `VideoCaption` | caption list, tags, and a framewise summary | action label or dense scene layout |
| "What action is happening?" | `ActionRecognition` | one Kinetics class label | a long natural-language description |
| "Dense caption" / object-heavy detail | `DenseCaption` | timestamped object-name descriptions | a final edited clip |
| "Cut video to TikTok" / `GenerateTikTokVideo` | `VideoCaption` + `ActionRecognition` + `DenseCaption` + composite TikTok flow | a new mp4 clip and narration artifacts | success without OpenAI, ffmpeg, or Bark |

## Workflow notes

### 1) Upload and pre-caption
- Use this when the user has just uploaded a local clip or wants the assistant to remember it for follow-up questions.
- The upload step keeps a renamed local video copy so later turns can refer to a stable file name.
- If captioning is loaded, pre-captioning happens automatically and the conversation memory gets a richer description.
- If captioning is not loaded, keep the upload valid and fall back to a generic video note.

### 2) Caption a video
- Use `VideoCaption` for a natural-language summary, tags, or a rough timeline.
- Return the caption list and tags first; add the framewise summary only if the user wants temporal structure.
- The timeline text is approximate and based on sampled frame positions, not a precise clock.

### 3) Recognize the action
- Use `ActionRecognition` when the user wants the main action class and nothing else.
- Keep this as the minimal video-only plan when possible.
- A single local video file is enough; no narration or ffmpeg step is needed.

### 4) Produce dense captions
- Use `DenseCaption` when the user wants many object cues, scene fragments, or other dense per-frame detail.
- This is useful when the clip has visually rich scenes and a single class label would be too coarse.
- Treat the output as dense object-name descriptions rather than polished prose.

### 5) Generate a TikTok-style clip
- Use this only when the user explicitly wants a highlight cut, a short-form edit, or a narrated social clip.
- The composite flow depends on the three analysis tools plus external runtime helpers.
- A valid plan needs:
  - `VideoCaption`
  - `ActionRecognition`
  - `DenseCaption`
  - an OpenAI key
  - ffmpeg
  - Bark
- The input format is a comma-separated pair: `video_path, prompt`.
- The output is the final mp4 clip; temporary wav and clip files are expected side effects.
- If the prerequisites are missing, stop at the best available analysis output instead of pretending the final clip was created.

## Static validation helper

Use `scripts/validate_video_plan.py` when you want to sanity-check the plan before touching any heavy runtime path.

Example checks:

```bash
python scripts/validate_video_plan.py \
  --video samples/demo.mp4 \
  --tool ActionRecognition \
  --uniformerv2-ready
```

```bash
python scripts/validate_video_plan.py \
  --video samples/demo.mp4 \
  --tool VideoCaption \
  --tool ActionRecognition \
  --tool DenseCaption \
  --tool GenerateTikTokVideo \
  --prompt "cut the most exciting part" \
  --tag2text-ready \
  --uniformerv2-ready \
  --detectron2-ready \
  --grit-checkpoint-ready \
  --openai-key-present \
  --ffmpeg-present \
  --bark-present
```

## Boundary reminders

- App launch flags, tab selection, and service deployment belong to the app deployment sibling skill.
- Image, audio, and DragGAN requests belong to their own sibling skills.
- This sub-skill stays focused on video inputs and video outputs.
