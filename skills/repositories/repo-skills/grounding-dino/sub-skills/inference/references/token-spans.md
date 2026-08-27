# Token Spans For GroundingDINO Inference

Token spans target exact character ranges in a prompt. Use them when a prompt is a sentence and the user wants detections for specific phrases, such as `a cat` and `a dog`, without relying on threshold-based phrase extraction.

## Span Schema

The CLI and underlying positive-map utility expect a list of phrase groups:

```text
[
  [[start, end], [start, end]],
  [[start, end]]
]
```

- The outer list has one item per phrase to detect.
- Each phrase group has one or more `[start, end]` character spans.
- `start` is inclusive and `end` is exclusive, matching Python slicing.
- Spans are offsets into the normalized caption used for inference.
- Each span should select visible non-whitespace text.

Example prompt:

```text
There is a cat and a dog in the image .
012345678901234567890123456789012345678
```

Example spans:

```bash
--text-prompt "There is a cat and a dog in the image ." \
--token-spans "[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]"
```

These phrase groups select:

| Span group | Slices | Phrase |
| --- | --- | --- |
| `[[9, 10], [11, 14]]` | `caption[9:10]`, `caption[11:14]` | `a cat` |
| `[[19, 20], [21, 24]]` | `caption[19:20]`, `caption[21:24]` | `a dog` |

## Caption Normalization Matters

GroundingDINO inference normalizes prompts by lowercasing, stripping whitespace, and appending a final period when missing. The bundled helper validates spans against that normalized caption.

Implications:

- If the input prompt lacks a final period, span offsets may shift because the helper appends one at the end.
- Case changes do not change offsets, but trimming leading/trailing whitespace does.
- For easiest span math, write the prompt exactly as it should be used, including the final period and spaces before separators.

## CLI Behavior

When `--token-spans` is provided to `scripts/grounding_dino_infer.py`:

- `--text-threshold` is ignored.
- `--box-threshold` filters phrase-specific logits.
- Spans are parsed with `ast.literal_eval`, not `eval`.
- The helper rejects malformed literals, out-of-range offsets, empty phrase groups, non-integer offsets, reversed ranges, and whitespace-only spans before loading weights.
- After tokenization, the helper also rejects span groups that do not align with tokenizer tokens.

Validation-only span check:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/cat_dog.jpeg \
  --text-prompt "There is a cat and a dog in the image ." \
  --token-spans "[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]" \
  --output-dir outputs/span-check \
  --cpu-only \
  --validate-only
```

## Python API Notes

The public `predict` function does not expose token spans. Token-span mode in the bundled helper mirrors the demo workflow by calling `groundingdino.util.vl_utils.create_positive_map_from_span(tokenized, token_span, max_text_len=256)` and multiplying phrase maps by query logits.

If writing your own token-span code:

1. Normalize the caption exactly once.
2. Run the model with `outputs = model(image[None], captions=[caption])`.
3. Use `outputs["pred_logits"].sigmoid()[0]` and `outputs["pred_boxes"][0]`.
4. Build positive maps with `model.tokenizer(caption)` and the span list.
5. Compute phrase logits with `positive_maps @ logits.T`.
6. Filter each phrase by `box_threshold`.
7. Keep boxes in normalized `cxcywh` until drawing or exporting.

## Common Span Failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `malformed token spans` | The value is not a Python literal list or has unmatched brackets/quotes. | Quote the whole value in the shell and use list syntax like `"[[[9, 10], [11, 14]]]"`. |
| `outside caption bounds` | Offsets were computed on a different caption string. | Recompute offsets after stripping and after adding the final period. |
| `selects only whitespace` | A span lands on spaces between words. | Adjust start/end so each slice contains phrase text. |
| `did not align with tokenizer tokens` | Character offsets hit punctuation/spacing that the tokenizer cannot map. | Expand or contract the span by one character to cover the word token. |
| No detections for a valid span | The phrase is not visible, threshold is too high, or checkpoint/config is wrong. | Lower `--box-threshold`, verify image content, and verify model files. |
