# Media Workflows

## Image generation and editing

Use image generation when the user asks for a new image from a text prompt. GPT Academic docs note DALL-E style workflows require switching to a GPT/OpenAI-compatible model family and having valid provider credentials.

For uploaded image understanding, select a vision-capable model. Do not promise image understanding from text-only local models.

## Voice assistant

Voice assistant setup needs audio enabled, browser microphone permission, and speech recognition credentials. Browser mic access usually requires localhost or HTTPS. Treat credential setup separately from model chat setup.

## Audio/video summary

For audio or video summaries, confirm the file is visible to the server and in a supported format. `ffmpeg` may be needed for conversion. Long media should be split or summarized in chunks.

## TTS

Edge TTS is a network-backed, no-GPU path that also needs `edge-tts`, `pydub`, and `ffmpeg`. SoVITS is an optional local/external service path that usually needs Docker/GPU or a running API endpoint.

## Video resources and animation

Video resource search is network/model backed and may rely on external media sites. Manim animation generation is local-rendering heavy and should be scoped to short scenes with clear prompts.
