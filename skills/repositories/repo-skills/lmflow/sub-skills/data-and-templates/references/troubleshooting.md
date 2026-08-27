# Data and Template Troubleshooting

## Missing `type` or `instances`

**Symptom**: validation fails with a message about `type` or `instances`.

**Cause**: the JSON file is not a valid LMFlow dataset object.

**Recovery**:

1. Add the top-level `type`.
2. Add the top-level `instances` array.
3. Re-run `scripts/validate_lmflow_dataset.py`.

## Mixed Types in One Directory

**Symptom**: one JSON file says `conversation` and another says `text2text`.

**Cause**: a dataset directory contains incompatible LMFlow types.

**Recovery**: split the files into separate directories or normalize them to one type.

## Conversation Formatting Problems

**Symptom**: the model sees malformed turns, empty messages, or a final unmatched user turn.

**Cause**: the conversation data does not match LMFlow's expected `messages` shape.

**Recovery**:

- ensure every message has `role` and `content`;
- alternate user and assistant turns;
- use `empty` or `empty_no_special_tokens` only when the prompt already contains the right markers.

## Multimodal Missing Dependency

**Symptom**: `Multimodal not available` or an image-related import error.

**Cause**: the `multimodal` extra or Pillow is missing.

**Recovery**: install the multimodal extra and confirm the image folder path is correct.

## Template Name Problems

**Symptom**: a template name is rejected or the output formatting looks wrong.

**Cause**: the selected template does not exist in `PRESET_TEMPLATES` or the installed Transformers version does not support the requested Jinja template.

**Recovery**: run `scripts/list_lmflow_templates.py` and choose a supported name.
