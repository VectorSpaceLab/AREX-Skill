---
name: video-understanding
description: "Guide video upload, captioning, action recognition, dense
  captioning, and TikTok-style clip generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# video-understanding

Use this sub-skill for local video requests such as caption this video, action recognition, dense caption, GenerateTikTokVideo, cut video to TikTok, or uploading a clip for later discussion.

Read [references/video-workflows.md](references/video-workflows.md) when choosing between upload, caption, action, dense, or TikTok flows.
Read [references/video-tool-reference.md](references/video-tool-reference.md) when you need the exact input/output contract, timeline format, or checkpoint map for a specific video tool.
Read [references/troubleshooting.md](references/troubleshooting.md) when a checkpoint, CUDA/VRAM limit, ffmpeg, Bark, or OpenAI prerequisite is missing.
Run [scripts/validate_video_plan.py](scripts/validate_video_plan.py) to statically check a video path, requested tool names, and TikTok prerequisites before any runtime plan.

## Scope

- In scope: video upload state, optional pre-captioning, Tag2Text captions/tags, InternVideo action recognition, GRiT dense captions, TikTok-style clip generation, and artifact naming.
- Out of scope: app launch/load flags, HTTPS/service deployment, and non-video modalities.

## Routing hints

- If the request is about app launch, load strings, tabs, or other service flags, hand it to `../app-deployment/SKILL.md`.
- If the request is image, audio, or DragGAN work, use the sibling modality skill instead of this one.

## Expected outputs

- Uploaded videos become renamed local copies in the app's working media area.
- Captioning returns caption text plus tag lists and framewise detail strings.
- Action recognition returns a Kinetics class label.
- Dense captioning returns timestamped object-name descriptions.
- TikTok generation returns a new mp4 clip plus temporary clip and audio artifacts.

## Guards

- Do not claim a video result without its required checkpoint, codec, or external tool.
- Do not promise TikTok generation when OpenAI, ffmpeg, or Bark is unavailable.
- Do not import or invoke heavy models from this skill; use the runtime tool plan only.
