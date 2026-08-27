# Pretraining Data Layout

## Vision-language examples

- Mixed rows include image base64, caption, question, answer, ground-truth objects, dataset name, and task type.
- This family is used for visual grounding, grounded captioning, image-text matching, image captioning, and VQA-style pretraining.

## Text-only examples

- Two columns: an ID and a text string.
- Used for text infilling.

## Image-only examples

- Typically an ID, a base64 image, and an image-code string.
- The image-code portion should be an integer sequence.

## Detection examples

- An ID, a base64 image, and bounding-box annotations.
- Each annotation usually contains coordinates plus object metadata.

## Negative-sample directory

- `all_captions.txt`: captions for contrastive or negative sampling.
- `object.txt`: object labels for substitution.
- `type2ans.json`: answer-type mapping for image-text matching logic.

## Validation tips

- Validate all files as a bundle, not one at a time.
- A complete workspace can still fail if one selected-column setting is off by one.
- If a file exists but the task still fails, check whether it is in the right pretraining role.
