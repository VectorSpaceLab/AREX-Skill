# Media Backend Matrix

| Workflow | Required backend/config | Notes |
| --- | --- | --- |
| DALL-E image generation/editing | OpenAI-compatible model/API key and network/proxy | switch to GPT-family model before use |
| Vision image understanding | vision model such as GPT-4o/GLM-4V/equivalent | text-only models cannot inspect images |
| Voice assistant | `ENABLE_AUDIO`, Aliyun speech credentials or configured speech provider, browser mic permission | use HTTPS or localhost for mic access |
| Edge TTS | `TTS_TYPE=EDGE_TTS`, `EDGE_TTS_VOICE`, `edge-tts`, `pydub`, `ffmpeg`, network | native `tests/test_tts.py` exercises this path but requires network/ffmpeg |
| SoVITS TTS | `TTS_TYPE=LOCAL_SOVITS_API`, `GPT_SOVITS_URL`, running SoVITS service | optional external service, often GPU/Docker |
| Audio/video summary | LLM provider, media reader/conversion tools, optional `ffmpeg` | long media can be expensive |
| Manim animation | Manim and rendering dependencies; optional system media tools | run only small scenes unless user approves cost/time |
| Multimedia agent | model + media dependencies for the selected task | treat as experimental/test-oriented when docs say so |

Use root `scripts/check_media_backends.py --repo-root <checkout>` before live media workflows.
