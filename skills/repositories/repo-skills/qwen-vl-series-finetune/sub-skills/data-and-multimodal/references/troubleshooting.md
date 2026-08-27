# Troubleshooting

## Symptom: media paths do not resolve

Likely cause:

- `image_folder` or `eval_image_folder` is wrong.
- The JSON mixes absolute and relative paths unexpectedly.

Fix:

- Re-run the bundled validator with `--check-media-paths`.
- Make sure the media folder matches the JSON references.

## Symptom: reasoning mode rejects samples

Likely cause:

- The model family does not support reasoning.
- A `Qwen3-VL-*-Thinking` sample is missing `reasoning`.
- DPO has only one reasoning field in the pair.

Fix:

- Confirm the model family in `references/model-compatibility.md`.
- Add or remove reasoning fields to match the target family.

## Symptom: video validation is confusing

Likely cause:

- Both `fps` and `nframes` are set.
- The media list was flattened incorrectly.

Fix:

- Choose one video sampling strategy.
- Keep the media field shape consistent across the dataset.

## Symptom: classification labels look wrong

Likely cause:

- The dataset label names do not match the expected class map.

Fix:

- Normalize labels before handing the dataset to the classification sub-skill.
