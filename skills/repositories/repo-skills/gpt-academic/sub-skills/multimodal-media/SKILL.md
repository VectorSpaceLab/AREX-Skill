---
name: multimodal-media
description: "Operate GPT Academic image, voice, audio, video, TTS, multimedia
  agent, and animation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Multimodal Media

Use this sub-skill when GPT Academic is asked to generate or understand images, use voice input, summarize audio/video, produce TTS audio, search video resources, use a multimedia agent, or create Manim animations.

## Trigger phrases

Read this sub-skill for “DALL-E”, “图片生成”, “image generation”, “vision model”, “voice assistant”, “实时语音对话”, “audio summary”, “video resource”, “Bilibili”, “Edge TTS”, “SoVITS”, “ffmpeg”, “Manim”, “数学动画”, or “多媒体智能体”.

## First decisions

1. Classify the task as image generation, image understanding, voice input, audio/video summary, TTS, video-resource search, multimedia agent, or animation.
2. Check media dependencies and backend config:

```bash
python scripts/check_media_backends.py --repo-root <checkout>
python sub-skills/multimodal-media/scripts/plan_media_workflow.py "<user request>" --file <optional-media-file>
```

3. Confirm provider credentials and browser/system permissions before live media calls.
4. If the prompt is text-only search/chat, route to `../conversation/SKILL.md`; if it is code execution, route to `../agent-tooling/SKILL.md`.

## Route map

| User goal | GPT Academic workflow | Read next |
| --- | --- | --- |
| generate/edit images | DALL-E image generation/edit plugins | `references/workflows.md`, `references/media-backends.md` |
| analyze image input | vision-capable model in chat/multimedia query | `references/media-backends.md` |
| use microphone/voice assistant | voice assistant audio path | `references/workflows.md`, `references/troubleshooting.md` |
| summarize audio/video | audio/video summary plugin | `references/workflows.md` |
| text-to-speech | Edge TTS or local SoVITS API | `references/media-backends.md` |
| find media/video resources | video resource GPT / multimedia agent | `references/workflows.md` |
| generate animation | Manim animation plugin | `references/media-backends.md` |

## Optional backend note

Media workflows are among the most backend-sensitive GPT Academic features. Edge TTS needs network and `ffmpeg`; Aliyun speech needs credentials; SoVITS usually needs an external service; DALL-E needs a GPT/OpenAI-compatible provider; Manim needs local rendering tools. Keep these as optional checks, not requirements for text-only GPT Academic use.
