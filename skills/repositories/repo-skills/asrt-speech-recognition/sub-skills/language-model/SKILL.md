---
name: language-model
description: "Route ASRT pinyin sequences through its statistical
  pinyin-to-Chinese language model."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# language-model

Use this sub-skill when a task needs ASRT's pinyin-to-Chinese text stage:

- decode a tone-number pinyin token list such as `ni3 hao3 ya5` to Chinese text;
- post-process pinyin emitted by an ASRT acoustic model;
- inspect or debug the bundled unigram/bigram language-model counts;
- maintain `pinyin_stream_decode` state across streaming chunks.

Do **not** use this sub-skill for audio loading, feature extraction, acoustic pinyin generation, or RPC wrapper design. Route acoustic pinyin generation to the `acoustic-models` sub-skill, audio and dictionary basics to `data-and-features`, and HTTP/gRPC endpoint wrappers to `serving-clients`.

## Runtime assets

This sub-skill is self-contained and includes the files required by the ASRT language model:

- `dict.txt` — tone-number pinyin to candidate Chinese characters;
- `language_model/language_model1.txt` — unigram character counts;
- `language_model/language_model2.txt` — bigram character counts;
- `scripts/decode_pinyin.py` — standalone decoder adapted from ASRT's language-model implementation.

## Start here

1. For workflows and model behavior, read `references/pinyin-language-model.md`.
2. For API signatures and state formats, read `references/api-reference.md`.
3. For failure diagnosis, read `references/troubleshooting.md`.
4. For a quick self-contained decode, run:

```bash
python scripts/decode_pinyin.py ni3 hao3 ya5
```

Expected output:

```text
你好呀
```
