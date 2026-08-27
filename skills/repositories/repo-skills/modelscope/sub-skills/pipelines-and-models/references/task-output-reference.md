# Task and Output Reference

This reference helps choose `Tasks` constants and read pipeline results using
standard `OutputKeys`.

## `Tasks`

`modelscope.utils.constant.Tasks` is a combined namespace of task strings from
computer vision, NLP, audio, multi-modal, science, and other domains. Use a
constant when available rather than repeating a literal string:

```python
from modelscope.utils.constant import Tasks

Tasks.word_segmentation       # 'word-segmentation'
Tasks.portrait_matting        # 'portrait-matting'
Tasks.text_classification     # 'text-classification'
Tasks.text_generation         # 'text-generation'
Tasks.chat                    # 'chat'
Tasks.image_classification    # 'image-classification'
```

`Tasks.find_field_by_task(task_name)` returns the broad registry field such as
`cv`, `nlp`, `audio`, `multi-modal`, or `science`. Preprocessor construction uses
this field to select the `PREPROCESSORS` registry group.

## Input checks

The base `Pipeline` checks input shapes for tasks listed in its task-input map.
Examples:

- `Tasks.text_classification`: accepts a text string, a `(text, text2)` tuple, or
  a dict with `text`/`text2`.
- `Tasks.word_segmentation`: accepts a text string or `{'text': ...}`.
- `Tasks.text_generation`: accepts text.
- `Tasks.chat`: accepts `{'messages': [...]}`; LLM pipeline classes may also
  convert a list of messages into that dict shape.
- Vision tasks usually accept paths, URLs, PIL images, or arrays depending on the
  task and preprocessor.

If a task lacks an input definition, ModelScope warns once rather than failing.
Custom smoke-test tasks can use a new task string, but production user workflows
should prefer existing `Tasks` constants.

## `OutputKeys`

Import constants from `modelscope.outputs`:

```python
from modelscope.outputs import OutputKeys
```

Common keys:

| Constant | Runtime string | Typical value |
| --- | --- | --- |
| `OutputKeys.SCORES` | `scores` | list or array of scores |
| `OutputKeys.SCORE` | `score` | single score |
| `OutputKeys.LABELS` | `labels` | list of labels |
| `OutputKeys.LABEL` | `label` | single label |
| `OutputKeys.TEXT` | `text` | generated, recognized, or transformed text |
| `OutputKeys.OUTPUT` | `output` | task-specific structured output |
| `OutputKeys.OUTPUT_IMG` | `output_img` | image array or image-like output |
| `OutputKeys.OUTPUT_IMGS` | `output_imgs` | list of image outputs |
| `OutputKeys.OUTPUT_VIDEO` | `output_video` | video/bytes output |
| `OutputKeys.OUTPUT_WAV` | `output_wav` | audio waveform/path/pcm output |
| `OutputKeys.BOXES` | `boxes` | detection boxes |
| `OutputKeys.MASKS` | `masks` | segmentation masks |
| `OutputKeys.KEYPOINTS` | `keypoints` | keypoints array/list |
| `OutputKeys.TEXT_EMBEDDING` | `text_embedding` | embedding array |
| `OutputKeys.IMG_EMBEDDING` | `img_embedding` | image embedding array |
| `OutputKeys.RESPONSE` | `response` | response dict/object |
| `OutputKeys.HISTORY` | `history` | conversation/history object |

## Representative task output expectations

The base output checker uses `TASK_OUTPUTS` for many tasks. Representative
examples:

| Task | Required keys |
| --- | --- |
| `Tasks.image_classification` | `scores`, `labels` |
| `Tasks.text_classification` | `scores`, `labels` |
| `Tasks.sentiment_classification` | `scores`, `labels` |
| `Tasks.sentence_similarity` | `scores`, `labels` |
| `Tasks.word_segmentation` | `output` |
| `Tasks.text_generation` | `text` |
| `Tasks.chat` | usually text-generation style keys or pipeline-specific response |
| `Tasks.text_summarization` | `text` |
| `Tasks.fill_mask` | `text` |
| `Tasks.auto_speech_recognition` | `text` |
| `Tasks.ocr_recognition` | `text` |
| `Tasks.portrait_matting` | `output_img` |
| `Tasks.universal_matting` | `output_img` |
| `Tasks.image_deblurring` | `output_img` |
| `Tasks.image_colorization` | `output_img` |
| object detection tasks | often `scores`, `labels`, `boxes` |
| segmentation tasks | often `scores`, `labels`, `masks` or `output_img` |

Use this table as a starting point, not a full schema. A pipeline may return
extra keys; task families can differ. For robust code:

```python
missing = [key for key in expected if key not in result]
if missing:
    raise ValueError(f"Missing {missing}; available keys: {list(result)}")
```

## Batched outputs

`p([a, b, c])` returns a list of result dicts when no `batch_size` is passed.
`p([a, b, c], batch_size=2)` also returns a list, but forward is called on
chunks. Do not assume a batched call returns a single dict unless using a
pipeline class whose documented behavior explicitly says so.

For `MsDataset` inputs, the base pipeline returns a generator. Iterate or call
`next(...)`; do not index it as a list.
