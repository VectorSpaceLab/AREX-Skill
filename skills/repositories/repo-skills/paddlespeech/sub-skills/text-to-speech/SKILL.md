---
name: text-to-speech
description: "Use PaddleSpeech TTS acoustic models, vocoders, ONNX/static
  inference, multilingual options, and training recipe guidance safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Text-to-Speech

Use this sub-skill for `paddlespeech tts`, `TTSExecutor`, acoustic/vocoder pairing, multi-speaker and multilingual options, ONNX/static choices, TTS training or synthesis recipe planning, voice cloning/SVS orientation, and TTS-specific troubleshooting.

## Common Routes

- **Simple synthesis**: read `references/cli-and-api.md`, then run `paddlespeech tts --input ... --output output.wav` after approving model downloads.
- **Choose AM/VOC/lang**: read `references/model-combinations-and-training.md` before mixing acoustic models, vocoders, `--lang`, and `--spk_id`.
- **Batch Chinese synthesis**: use `scripts/build_tts_job.py` for whitespace-free text job files; use direct quoted `--input` for English/spaced text.
- **ONNX or streaming TTS**: use this sub-skill for model pairing, then route to `../deployment-serving/SKILL.md` for server config and streaming protocols.
- **Training/fine-tuning recipes**: read `references/model-combinations-and-training.md`; ask before dataset downloads, GPU jobs, or staged recipe execution.
- **Text frontend, G2P, TN, MFA**: route to `../text-processing/SKILL.md` when the task is text preparation rather than synthesis itself.

## Safe Workflow

```bash
paddlespeech tts --input "你好，欢迎使用百度飞桨深度学习框架！" --output output.wav
paddlespeech tts --am fastspeech2_ljspeech --voc hifigan_ljspeech --lang en --input "Life was like a box of chocolates." --output en.wav
paddlespeech tts --am fastspeech2_aishell3 --voc hifigan_aishell3 --lang zh --spk_id 0 --input "你好" --output spk0.wav
```

Before running, confirm:

1. The AM/VOC/lang combination exists.
2. A pretrained run may download both AM and vocoder archives.
3. The output extension is a writable `.wav` path.
4. CPU can work but may be slow; GPU requires a matching PaddlePaddle GPU runtime.

## References and Helper

- `references/cli-and-api.md` covers TTS CLI options, Python executor, ONNX flags, and output behavior.
- `references/model-combinations-and-training.md` maps acoustic/vocoder choices, language/multispeaker constraints, and recipe structure.
- `references/troubleshooting.md` covers model pairing, frontend, dictionary/stat, ONNX, output, and batch parsing errors.
- `scripts/build_tts_job.py` builds safe `.job` files for text without whitespace.

## Do Not Do by Default

- Do not run full TTS/vocoder training recipes, voice cloning, VC, SVS, VITS, or JETS recipes without approval.
- Do not claim ONNX/Paddle Lite/Android/C++ deployment is verified from a dynamic Python synthesis check.
- Do not use `.job` for English text with spaces unless you have verified the target parser accepts it; direct `--input` is safer.
