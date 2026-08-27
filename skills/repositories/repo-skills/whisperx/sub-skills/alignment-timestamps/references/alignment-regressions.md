# Alignment regressions and timestamp interpolation

## Purpose

Read this when word timestamps are missing for digits, comma decimals, symbols, mixed alphanumeric words, or when deciding between `nearest`, `linear`, and `ignore` interpolation.

This guidance distills package regression behavior into runtime knowledge. It does not require future agents to open the original tests.

## Core regression behavior

The alignment implementation keeps transcript characters that are not in the alignment model dictionary, rather than dropping them. When at least one such unknown character appears, it extends the CTC emission with a wildcard column computed from the best non-blank score at each frame. Unknown characters then align through that wildcard token.

Practical impact:

- Words made only of digits, such as `43`, can receive `start`, `end`, and `score` when the CTC path is usable.
- Mixed words, such as `43k`, can receive timestamps without corrupting neighboring known words.
- Comma decimal text, including German-style `4,9`, is covered by the same wildcard path.
- Neighbors around unknown words should still keep valid, monotonic timestamps.

## Regression-backed scenarios

| Scenario | Text pattern | Expected assertion |
| --- | --- | --- |
| Baseline known words | `the cat sat` | Every word has `start`, `end`, and `score`. |
| All-unknown word | `cost 43 dollars` | The word `43` appears in `word_segments` and has timestamps/score. |
| Mixed unknown/known word | `has 43k users` | The word `43k` appears and has timestamps. |
| Neighbor preservation | `cost 43 dollars` | `cost` and `dollars` keep timestamps and scores. |
| All-unknown segment | `123 456` | Word segments are still produced and have timestamps when wildcard CTC succeeds. |
| Monotonic order | `the 99 cats` | Word starts are monotonically non-decreasing. |
| German comma decimal | `halt mit 4,9 nicht ins parlament` | The word `4,9` has `start`, `end`, and `score`. |
| Ignore interpolation | `the 99 cats` with `interpolate_method="ignore"` | Alignment does not crash; known words keep timestamps; segment start/end remain valid floats. |

Run the bundled checker for a safe approximation of the comma-decimal case:

```bash
python scripts/check_alignment_contract.py --text "cost 4,9 dollars" --required-word "4,9"
python scripts/check_alignment_contract.py --interpolate-method ignore --text "halt mit 4,9 nicht ins parlament" --required-word "4,9" --language de
```

The checker uses a synthetic CTC emission and a mock torchaudio-style model. Passing it proves the local installed aligner still satisfies the wildcard contract under synthetic conditions; it does not prove a real model will produce high-quality timestamps for arbitrary audio.

## Interpolation behavior

WhisperX calls `interpolate_nans` for missing word and sentence timestamps.

| Method | Behavior | Use when |
| --- | --- | --- |
| `nearest` | Fills NaNs by nearest interpolation, with forward/back fill when enough timestamps exist. This is the default. | You want practical word timestamps even when a few words are unalignable. |
| `linear` | Fills NaNs with linear interpolation, then forward/back fill. | You prefer a smoother progression across gaps and have surrounding timestamps. |
| `ignore` | Returns the same series without filling NaNs. Guarded assignment means unaligned words may remain without `start`/`end`. | You need to distinguish model-aligned words from interpolated words, or you are auditing timestamp confidence. |

If there is only one non-null timestamp in a series, non-`ignore` methods fall back to forward/back filling from that single value.

## Reconciling old limitations with current behavior

Public documentation historically warned that words containing no characters in the alignment dictionary, such as numeric or currency strings, cannot be aligned and therefore may not receive timing. The current alignment path mitigates many of these cases using wildcard CTC handling. Treat the combined guidance as:

- Digits, commas, and symbols are no longer automatically hopeless; test them with the bundled checker and a representative real alignment model.
- A word can still lack timestamps if the segment has no usable characters, the audio slice is invalid, the start time is beyond the audio duration, CTC backtracking fails, or `interpolate_method="ignore"` preserves missing values.
- For production or evaluation work, assert the exact words you need and inspect `word_segments`; do not infer success from the presence of segment-level timestamps alone.

## Practical assertion pattern

```python
aligned = whisperx.align(
    result["segments"],
    model_a,
    metadata,
    audio,
    device,
    interpolate_method="nearest",
)
words = {w["word"]: w for w in aligned["word_segments"]}
for required in ["4,9"]:
    word = words.get(required)
    if word is None or "start" not in word or "end" not in word:
        raise AssertionError(f"missing timestamp for {required!r}: {word}")
```

## Difficult cases to plan for verification

1. **German numeric comma timestamp case**: build a synthetic or cached-model case with `language_code="de"`, text containing `4,9`, and assertions that the numeric word has `start`, `end`, `score`, and does not break neighbor word order.
2. **Custom Hugging Face alignment model case**: use a non-default `model_name` for a language without automatic default coverage, prove the model/processor are available in cache or allow a controlled download, then assert aligned word timestamps on a short representative transcript.
