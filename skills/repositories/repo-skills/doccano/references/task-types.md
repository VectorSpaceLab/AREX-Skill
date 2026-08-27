# Supported project types

doccano supports several task families. The project type controls the annotation shape, the page route, and which import/export formats are valid.

| Project type | Annotation shape | Typical UI route | Notes |
| --- | --- | --- | --- |
| `DocumentClassification` | Category labels on text | `projects/<id>/text-classification` | Supports single-label or multi-label classification depending on project settings. |
| `SequenceLabeling` | Spans on text | `projects/<id>/sequence-labeling` | Can optionally enable overlapping spans and relations. |
| `Seq2seq` | Text-to-text labels | `projects/<id>/sequence-to-sequence` | Often used for summarization or translation-style outputs. |
| `IntentDetectionAndSlotFilling` | Categories plus spans | `projects/<id>/intent-detection-and-slot-filling` | Combined intent and slot annotation. |
| `Speech2text` | Audio file plus transcript labels | `projects/<id>/speech-to-text` | File-based task; the example data points to audio assets. |
| `ImageClassification` | Category labels on image files | `projects/<id>/image-classification` | Uses file-backed examples rather than plain text. |
| `BoundingBox` | `x`, `y`, `width`, `height`, label | `projects/<id>/object-detection` | The frontend route uses object-detection terminology for bounding boxes. |
| `Segmentation` | Polygon or point-region labels | `projects/<id>/segmentation` | Uses image-region annotations. |
| `ImageCaptioning` | Text captions for image files | `projects/<id>/image-captioning` | File-backed task with text labels. |

## Common project settings

- `collaborative_annotation`: shared vs per-user annotation visibility.
- `single_class_classification`: whether only one category may be chosen for document classification.
- `allow_overlapping`: whether spans may overlap in sequence labeling.
- `grapheme_mode`: span handling for grapheme-aware text workflows.
- `use_relation`: enables relation extraction on sequence labeling projects.
- `allow_member_to_create_label_type`: lets project members add labels.

## Practical routing notes

- Project creation, labels, members, comments, annotation, and metrics belong in `sub-skills/project-annotation/`.
- File import/export and format handling belong in `sub-skills/data-transfer/`.
- Setup of a new project usually starts in `sub-skills/setup-and-deploy/` only when the app itself is not yet running.
