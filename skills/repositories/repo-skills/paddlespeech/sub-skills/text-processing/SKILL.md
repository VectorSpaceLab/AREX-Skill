---
name: text-processing
description: "Use PaddleSpeech punctuation restoration, text frontend, G2P, text
  normalization, MFA, and tokenizer preparation workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Text Processing

Use this sub-skill for `paddlespeech text --task punc`, punctuation restoration models, text frontend preparation, G2P, text normalization, MFA/rhythm-tag orientation, and SentencePiece tokenizer recipe planning.

## Route by Intent

- **Restore punctuation in plain text**: use `references/punctuation-and-frontends.md` and `scripts/prepare_punctuation_input.py`.
- **Post-process an ASR transcript**: run ASR first via `../speech-to-text/SKILL.md`, then use punctuation restoration here.
- **Prepare TTS frontend resources**: use this sub-skill for G2P, text normalization, MFA, rhythm tags, and SentencePiece planning; return to `../text-to-speech/SKILL.md` for synthesis.
- **Run server text service**: route to `../deployment-serving/SKILL.md` after choosing the punctuation model/config.

## Safe Punctuation Workflow

```bash
python scripts/prepare_punctuation_input.py --text 今天的天气真不错啊你下午有空吗我想约你一起去吃饭
paddlespeech text --task punc --model ernie_linear_p3_wudao_fast --input 今天的天气真不错啊你下午有空吗我想约你一起去吃饭
```

The punctuation executor cleans unsupported characters and asserts that the remaining text is non-empty. Validate before running a model download.

## References and Helper

- `references/punctuation-and-frontends.md` covers punctuation CLI/API, ERNIE model choices, text frontend tools, G2P, TN, MFA, and SentencePiece recipe boundaries.
- `references/troubleshooting.md` covers unsupported input, model/tokenizer downloads, AIStudio/PaddleNLP mismatch, MFA/Kaldi side effects, and job parsing.
- `scripts/prepare_punctuation_input.py` validates and cleans punctuation input without loading PaddleSpeech models.

## Do Not Do by Default

- Do not run G2P/TN/MFA recipes that install external tools or require datasets unless approved.
- Do not treat punctuation restoration as language-agnostic; the released CLI models here are Chinese punctuation models.
- Do not run the text server as a substitute for local punctuation unless the user needs a service.
