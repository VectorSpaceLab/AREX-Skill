# Installation and runtime reference

## Purpose

Read this before installing or launching FunClip, preparing a no-network smoke
check, or deciding which optional runtime dependencies must be available.

## Baseline install

FunClip is a checkout-oriented Python application. From the repository root:

```bash
python -m pip install -r requirements.txt
```

The inspected v2.1.1 dependency manifest includes these important constraints:

| Surface | Requirement evidence | Why it matters |
| --- | --- | --- |
| FunASR compatibility | `funasr>=1.3.29` | Required for Fun-ASR-Nano/SenseVoice subtitle and `sentence_info` compatibility paths. |
| Gradio runtime | `gradio>=4.31.3,<5.0`, `starlette<1.0` | Prevents fresh Gradio 4 installs from pulling an incompatible Starlette 1.x template API. |
| Media handling | `moviepy==1.0.3`, `librosa`, `soundfile`, `numpy==1.26.4` | Needed for audio extraction, resampling, clip generation, and SRT/subtitle helpers. |
| ASR/model stack | `torch>=1.13`, `torchaudio`, `transformers`, `huggingface_hub`, `modelscope` | Needed for FunASR model loading and model-cache access. |
| Provider SDKs | `openai`, `dashscope`, `g4f`, `twelvelabs>=1.2.8` | Needed by LLM provider routes. |
| LiteLLM optional route | `litellm>=1.83.0` when using or testing LiteLLM | The repo helper imports LiteLLM lazily and reports this install hint when missing. |

Python 3.11 was used for the inspection environment. The repository does not
publish a Python-version range in package metadata, so prefer a modern Python
supported by the listed wheels and rerun the bundled smoke check after changes.

## Launching

Default local Gradio app:

```bash
python funclip/launch.py
```

Common model choices:

```bash
python funclip/launch.py -m fun-asr-nano
python funclip/launch.py -m sensevoice
python funclip/launch.py -l en
```

Remote/container binding:

```bash
python funclip/launch.py --listen --port 7860
python funclip/launch.py --listen --share --port 7860
```

`--listen` changes the bind address to `0.0.0.0` and disables the local browser
probe. It does not enable a public Gradio tunnel unless `--share` is also set.

## Model and data boundaries

- Model weights are downloaded or resolved separately when real recognition
  starts. Source archives and this skill do not bundle model weights.
- Real ASR can require network/cache access and enough CPU/GPU memory for the
  selected model, even though deterministic smoke checks use fake or mocked
  paths.
- Fun-ASR-Nano is useful for broad multilingual ASR, but precise text-based
  clipping should prefer Paraformer when character-level timestamps are needed.
- SenseVoice can return emotion/audio-event tags; FunClip strips rich tags from
  display text and uses compatible sentence/timestamp fallbacks when available.

## Media and subtitle prerequisites

Basic audio/video clipping uses MoviePy plus ffmpeg-compatible media support.
Subtitle burn-in additionally depends on ImageMagick text rendering and a usable
font. If subtitle overlay fails but clipping succeeds, keep `add_sub=False` or
fix ffmpeg/ImageMagick/font setup before retrying.

The original checkout contains a large font asset, but this generated skill does
not bundle it. For a deployed checkout, ensure the runtime can resolve the font
path expected by the FunClip script or adapt the runtime to a local font.

## LLM provider prerequisites

Provider routes need provider-specific keys and sometimes extra packages:

- OpenAI-compatible GPT/DeepSeek/AtlasCloud/MiniMax routes use the `openai`
  client. AtlasCloud and MiniMax have provider-specific environment fallbacks.
- Qwen routes use DashScope and expect a DashScope-compatible key.
- LiteLLM routes require installing `litellm>=1.83.0`.
- g4f is best-effort and can be unstable.
- TwelveLabs Pegasus needs `twelvelabs>=1.2.8`, a key, and a video input.

Read [../sub-skills/llm-providers/SKILL.md](../sub-skills/llm-providers/SKILL.md)
for provider-specific behavior.

## No-network skill smoke checks

Use the root helper first:

```bash
python scripts/check_environment.py --repo-root <funclip-checkout> --check-binaries
```

Then use sub-skill helpers as needed:

```bash
python sub-skills/clip-workflows/scripts/clip_cli_smoke.py --repo-root <funclip-checkout>
python sub-skills/llm-providers/scripts/provider_route_smoke.py --repo-root <funclip-checkout>
python sub-skills/release-packaging/scripts/build_release_assets.py --help
```

These checks are deterministic and do not download model weights, call external
LLM providers, or process real media unless the helper explicitly says so.
