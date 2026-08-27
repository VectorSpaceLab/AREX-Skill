# ASRT pinyin language-model workflow

ASRT separates speech recognition into two stages: an acoustic model emits a sequence of Chinese pinyin tokens, and the language model converts those tokens to Chinese characters. This sub-skill covers only the second stage.

## Required files and layout

The runtime decoder expects this self-contained layout:

```text
language-model/
  dict.txt
  language_model/
    language_model1.txt
    language_model2.txt
  scripts/
    decode_pinyin.py
```

`dict.txt` maps each tone-number pinyin syllable to candidate Chinese characters. `language_model1.txt` and `language_model2.txt` contain unigram and bigram counts used to score character sequences.

The original ASRT code loads `dict.txt` by name from the current working directory and loads `language_model1.txt`/`language_model2.txt` under `model_path`. The bundled script avoids that working-directory dependency by defaulting to the files above and by exposing explicit `--dict` and `--model-dir` options.

## Batch decoding

Use the bundled script for standalone pinyin-to-text decoding:

```bash
python scripts/decode_pinyin.py ni3 hao3 ya5
# 你好呀
```

The same input can come from standard input:

```bash
printf 'ni3 hao3 ya5\n' | python scripts/decode_pinyin.py --stdin
```

Use `--beam-size` to bound how many partial candidates survive after each bigram extension:

```bash
python scripts/decode_pinyin.py --beam-size 20 ni3 hao3 ya5
```

The default beam size is `100`, matching ASRT's server-side language-model use.

## Acoustic post-processing stage

When an acoustic model already produced a pinyin list, pass that list directly to the language model:

```python
from scripts.decode_pinyin import ModelLanguage

ml = ModelLanguage("language_model", dict_path="dict.txt")
ml.load_model()
text = ml.pinyin_to_text(["ni3", "hao3", "ya5"], beam_size=100)
assert text == "你好呀"
```

This stage does not load audio, compute spectrograms, or run CTC decoding. If the upstream task starts from audio samples, route that part to the acoustic/data sub-skills and return here only after a pinyin sequence exists.

## Streaming decode state

`pinyin_stream_decode(temple_result, item_pinyin, beam_size=100)` consumes one pinyin token at a time and returns a list of candidate states. Each state has the shape:

```python
[candidate_text, score]
```

For stream processing:

1. Keep `tmp_result_last` between pinyin tokens and between audio chunks.
2. For each pinyin token, call `pinyin_stream_decode(tmp_result_last, token, beam_size)`.
3. If the result is empty but the previous state was non-empty, commit the best previous candidate (`tmp_result_last[0][0]`) and restart the current token from an empty state.
4. At end of stream, commit the best remaining candidate if the state is non-empty.

The bundled script can show this state evolution:

```bash
python scripts/decode_pinyin.py --stream ni3 hao3 / ya5
```

The `/` token marks a chunk boundary for the CLI only; decoder state is preserved across chunks.

## Count and scoring behavior

The model is count-based rather than neural:

- `dict.txt`: `pinyin<TAB>characters`; candidate order matters for first-token ties.
- `language_model1.txt`: first line is a corpus total and is not used by the decoder; later lines are `character<TAB>count`.
- `language_model2.txt`: first line is a corpus total and is not used by the decoder; later lines are `two_character_sequence<TAB>count`.
- First token: every candidate character for the pinyin receives score `1.0`.
- Later tokens: a transition is allowed only when the previous character plus current candidate character exists in the bigram model.
- Transition score: `previous_score * bigram_count(previous_char + current_char) / unigram_count(previous_char)`.
- Candidate states are sorted by descending score after each extension and truncated to `beam_size`.

For `['ni3', 'hao3', 'ya5']`, the bundled counts contain `你好` and `好呀`, so the best decode is `你好呀`.

## Unknown and empty-intermediate behavior

If a pinyin token is not in `dict.txt`, `pinyin_stream_decode` returns an empty list. In batch `pinyin_to_text`, an empty intermediate after a non-empty previous state commits the best previous segment, attempts to restart from the current pinyin, commits that single-token candidate if it exists, and clears state. If the unknown token appears with no previous state, it contributes no output.

Use `--diagnose` to identify tokens absent from `dict.txt` before relying on a decode:

```bash
python scripts/decode_pinyin.py --diagnose ni3 unknown9 hao3
```
