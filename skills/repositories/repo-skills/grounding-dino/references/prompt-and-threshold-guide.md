# Prompts, Thresholds, And Token Selection

## Prompt Shape

GroundingDINO pairs an image with a text prompt. The public inference helper lowercases and strips captions, then appends a final period when missing. For class-like prompts, separate candidate categories with periods:

```text
cat . dog . person . traffic light .
```

Phrase prompts can be natural sentences, but class-list prompts are easier to debug because phrase boundaries are explicit.

## Thresholds

Common starting values are:

- `box_threshold=0.35` for single-image detection.
- `text_threshold=0.25` for phrase extraction.
- Lower thresholds can recover faint detections but increase false positives.
- Higher thresholds reduce noisy detections but can produce empty outputs.

If there are no detections, check the config/checkpoint pair, prompt wording, image preprocessing, device, and thresholds before assuming the model failed.

## Token Spans

Use token spans when the task needs detections for exact phrases inside a sentence rather than all words above `text_threshold`. Token spans are character offsets into the normalized caption, grouped by phrase:

```text
[[[11, 14]], [[21, 24]]]
```

For deeper examples and validation rules, read `../sub-skills/inference/references/token-spans.md`.

## Prompt Debug Checklist

1. Confirm the caption has explicit separators or phrase spans.
2. Confirm span offsets index the exact normalized prompt string.
3. Try a class-list prompt before a long sentence when debugging.
4. Lower `box_threshold` slightly if all predictions are filtered out.
5. Lower or raise `text_threshold` depending on phrase quality.
6. Verify the checkpoint matches the config variant.
