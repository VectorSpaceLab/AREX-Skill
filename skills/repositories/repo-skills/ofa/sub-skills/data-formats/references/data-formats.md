# Data Formats

## Purpose

Use this reference when you need to know which columns, payloads, or sidecar files OFA expects for a workflow.

## TSV families at a glance

| Workflow | Typical row shape | Key columns / values | Notes |
| --- | --- | --- | --- |
| Caption | `uniq_id, image_id, caption, predicted_objects, image_b64` or a family-specific variant | image payload is base64; caption text is plain text | The selected columns often ignore the predicted-object column during training but still require the row shape. |
| VQA | `question_id, image_id, question, answer_with_conf, object_labels, image_b64` | answer/confidence field often uses `conf|!+answer` | The answer-label mapping can come from a JSON file or a pickle file. |
| RefCOCO | `uniq_id, image_id, text, region_coord, image_b64` | region coordinates are comma-separated boxes | Coordinate format matters as much as the text/image fields. |
| SNLI-VE | `uniq_id, image_id, image_b64, hypothesis, caption/premise, label` | labels usually map to yes/no/maybe | The label string is later constrained through the task dictionary. |
| OCR | `uniq_id, image_b64, text` | image is base64, text is normalized Chinese or Latin text | Document-style resizing may be needed for some OCR inputs. |
| Image classification | `image_b64, class_id, synset_words` | class IDs are usually 1-indexed | The synset label string is used as the seq2seq target. |
| Gigaword | `source, target` | both are plain text | Metric helpers usually expect JSON result files after generation. |
| GLUE | usually `sentence_a, sentence_b, label` or task-specific variants | label is mapped to yes/no/maybe or no/yes depending on the task | Prompt type can change the target construction. |
| Pretraining | `vision_language_examples.tsv`, `text_examples.tsv`, `image_examples.tsv`, `detection_examples.tsv` | mixture-specific columns and negative samples | Validate the workspace as a whole, not just a single TSV. |
| MMSpeech | `speech_id, wav_path, text` | audio path must exist; config YAML must match feature extraction | Speech workflows need both the TSV and the fbank config to agree. |

## Common validation rules

- `selected_cols` must match the command that will read the TSV.
- Base64 image cells should decode to a Pillow image before you train.
- Image code sequences should be integer tokens, not comma-separated text or JSON.
- JSON fields such as `type2ans.json` or prediction files should be valid JSON before a metric helper tries to parse them.
- Path fields should exist before you launch a long job.

## Use the bundled helpers

- `scripts/encode_image_base64.py` for creating image cells.
- `scripts/validate_ofa_tsv.py` for general TSV checks.
- `sub-skills/pretraining/scripts/validate_pretraining_inputs.py` for the mixed pretraining bundle.
- `sub-skills/mmspeech/scripts/validate_mmspeech_manifest.py` for audio manifests.

## Task-specific reminders

- VQA and image classification often need answer/class mapping files in addition to the TSV.
- RefCOCO and OCR are sensitive to coordinate and normalization details.
- Text-to-image generation uses integer code sequences, not natural-language captions alone.
