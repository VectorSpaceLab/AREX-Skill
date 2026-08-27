---
name: asrt-speech-recognition
description: "Operate ASRT SpeechRecognition Chinese ASR data, acoustic models,
  pinyin language model, and serving clients."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# asrt-speech-recognition

Use this repo skill for tasks involving ASRT SpeechRecognition, a Chinese speech recognition system with ASRT-style WAV/data manifests, TensorFlow/Keras CNN+CTC acoustic models, a statistical pinyin-to-Chinese language model, and HTTP/gRPC serving clients.

## Route by task

| User task signal | Read |
| --- | --- |
| `asrt_config.json`, `dict.txt`, datalist/label format, `/data/speech_data`, WAV sample rate, spectrogram/MFCC/SpecAugment, `DataLoader`, CTC utility smoke checks | [sub-skills/data-and-features/SKILL.md](sub-skills/data-and-features/SKILL.md) |
| `SpeechModel251BN`, Keras CTC model shapes, `ModelSpeech`, training/resume/evaluation, `save_models`, single-file acoustic prediction, TensorFlow/GPU expectations, PyTorch backend caveats | [sub-skills/acoustic-models/SKILL.md](sub-skills/acoustic-models/SKILL.md) |
| Decode ASRT pinyin such as `ni3 hao3 ya5`, `ModelLanguage`, `language_model1.txt`, `language_model2.txt`, streaming pinyin-to-text state, unknown pinyin diagnosis | [sub-skills/language-model/SKILL.md](sub-skills/language-model/SKILL.md) |
| ASRT HTTP service, `/speech`, `/language`, `/all`, gRPC `AsrtGrpcService`, `asrt.proto`, payload construction, status codes, Docker/service deployment | [sub-skills/serving-clients/SKILL.md](sub-skills/serving-clients/SKILL.md) |

## First operating checks

1. Read [references/installation-and-runtime.md](references/installation-and-runtime.md) before installing dependencies or choosing CPU versus CUDA/GPU guidance.
2. Run the environment check when a user asks whether their runtime can operate ASRT modules:
   ```bash
   python scripts/check_asrt_runtime.py --help
   ```
3. Run the bundled self-contained smoke checks when validating this skill's helpers rather than a user's ASRT checkout:
   ```bash
   python scripts/run_asrt_smokes.py
   ```
4. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, data/model-file, TensorFlow, and dependency failures before drilling into a sub-skill.

## Cross-workflow recipes

### Validate ASRT data before training

Route to `data-and-features`, validate config/list/dict consistency, then route to `acoustic-models` only after the data map, sample rate, and pinyin labels are clean. Do not start a training recipe when the user is still missing list files, label rows, pinyin dictionary entries, or 16 kHz WAVs.

### Prepare an acoustic model run

Route to `acoustic-models` for model selection and weight naming. Use `data-and-features` for audio/features and `language-model` only after acoustic prediction has produced pinyin tokens. A CPU Keras construction smoke proves only model import/shape compatibility; it does not verify GPU training or accuracy.

### Decode pinyin text only

If the user already has pinyin tokens such as `ni3 hao3 ya5`, skip acoustic/audio guidance and use `language-model`. Its bundled decoder is self-contained and includes ASRT language-model count files.

### Build service clients

Route to `serving-clients` when the server is already prepared or the user is building a client. If startup fails because `save_models/SpeechModel251bn.model.h5` is missing, route back to `acoustic-models`. If payload WAV metadata is wrong, route to `data-and-features`.

## Boundaries and verification status

- This skill provides self-contained operating guidance and bundled helpers. It does not include trained acoustic weights or full speech corpora.
- Full training, evaluation accuracy, trained-weight prediction, live HTTP/gRPC round trips, and Docker builds require user-provided datasets/weights/services and are not claimed as verified by this skill alone.
- The generated language-model sub-skill bundles `dict.txt` plus `language_model1.txt` and `language_model2.txt` so pinyin-to-text decoding can be used without reopening the ASRT source tree.
- Repo provenance and routing metadata are in [references/repo-provenance.md](references/repo-provenance.md) and [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
