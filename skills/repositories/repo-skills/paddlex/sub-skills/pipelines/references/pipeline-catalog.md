# PaddleX pipeline catalog and operating notes

This reference distills PaddleX 3.7.2 pipeline usage from the package docs, configs, examples, and installed API inspection. It is intentionally self-contained; do not depend on the original checkout when using it.

## Public entry points

### Python API

```python
from paddlex import create_pipeline

pipeline = create_pipeline(
    pipeline="OCR",          # built-in name or local YAML path
    config=None,             # optional config dict
    device="cpu",            # e.g. "cpu", "gpu:0", "gpu:0,1"
    engine=None,             # backend/engine override
    engine_config=None,      # flat or nested engine options
    use_hpip=False,          # high-performance inference switch
    hpi_config=None,         # HPI config dict/object
)
for result in pipeline.predict(input_data):
    result.print()
```

The installed 3.7.2 signature is:

```text
create_pipeline(pipeline=None, *, config=None, device=None, engine=None,
                engine_config=None, pp_option=None, use_hpip=None,
                hpi_config=None, **kwargs) -> BasePipeline
```

`pipeline` can be a built-in pipeline name, a path to a local YAML file, or omitted when `config` supplies the pipeline definition. Pipeline-specific keyword arguments are accepted through `**kwargs`.

### CLI

```bash
paddlex --get_pipeline_config image_classification
paddlex --pipeline image_classification --input demo.jpg --save_path output --device cpu
paddlex --pipeline ./pipeline.yaml --input demo.jpg --save_path output
```

The installed CLI exposes these pipeline flags: `--pipeline`, `--input`, `--save_path`, `--engine`, `--device`, `--use_hpip`, `--hpi_config`, and `--get_pipeline_config`.

## Common pipeline families

Representative built-in YAML names found in the 3.7.2 config set:

| Family | Common names | Notes |
| --- | --- | --- |
| Image/CV | `image_classification`, `object_detection`, `instance_segmentation`, `semantic_segmentation`, `small_object_detection`, `rotated_object_detection`, `image_multilabel_classification`, `anomaly_detection`, `human_keypoint_detection`, `open_vocabulary_detection`, `open_vocabulary_segmentation` | Usually image or directory inputs; saves JSON and visualized images. |
| OCR/document | `OCR`, `doc_preprocessor`, `layout_parsing`, `PP-StructureV3`, `table_recognition`, `table_recognition_v2`, `formula_recognition`, `seal_recognition` | Often produces multiple artifact types: JSON, images, HTML, XLSX, Markdown. Prefer an output directory. |
| Information extraction / VLM | `PP-ChatOCRv3-doc`, `PP-ChatOCRv4-doc`, `PP-DocTranslation`, `PaddleOCR-VL`, `PaddleOCR-VL-1.5`, `PaddleOCR-VL-1.6`, `doc_understanding` | May require LLM/GenAI client configuration, model-server URL, credentials, or large VLM resources. Route server/backend setup to deployment. |
| Retrieval / face / attributes | `PP-ShiTuV2`, `face_recognition`, `pedestrian_attribute_recognition`, `vehicle_attribute_recognition` | Some workflows need a local gallery/index fixture before prediction. |
| Time series | `ts_forecast`, `ts_anomaly_detection`, `ts_classification` | CSV/tabular inputs; ensure timestamp/target columns match the exported config. |
| Speech | `multilingual_speech_recognition`, `text_to_speech` | Needs audio/text dependencies and appropriate input types. |
| Video | `video_classification`, `video_detection` | Needs a compatible video decoder/codec stack. In the construction env, `decord` was optional and not baseline-verified. |
| 3D | `3d_bev_detection` | Requires multi-modal/3D data layout and matching hardware/dependencies. |

## Config workflow

1. Export the nearest built-in config with `paddlex --get_pipeline_config NAME`.
2. Edit the YAML for model names, input/output settings, submodule behavior, or engine settings.
3. Run via CLI using `--pipeline ./edited.yaml`, or load the YAML/dict through the Python API.
4. Add explicit CLI/API overrides only for run-specific values such as `--device`, `--input`, `--save_path`, or one-off backend options.

Precedence to remember:

- explicit Python/CLI arguments override YAML defaults.
- `engine` is a direct engine override.
- `use_hpip` enables HPI selection where supported, but explicit engine/backend settings can take precedence.
- nested `engine_config` and `hpi_config` values should be attached at the level expected by the pipeline/submodule, not guessed globally.

## Prediction inputs

PaddleX pipelines are heterogeneous. Before running, classify the input shape:

- image URL/path, image directory, or in-memory image object.
- PDF or multi-page document.
- table/CSV for time-series tasks.
- audio file/URL for speech tasks.
- video file/URL for video tasks.
- dict/list inputs for document understanding, ChatOCR, retrieval index building, or GenAI-backed flows.

When uncertain, start with the pipeline's exported YAML and a single local file. Avoid running large directory batches until the single-case path is confirmed.

## Result saving patterns

Result objects usually support `print()`. Depending on the pipeline and result type, they may also support save helpers such as:

- `save_to_json(path)`
- `save_to_img(path)`
- `save_to_csv(path)`
- `save_to_html(path)`
- `save_to_xlsx(path)`
- `save_to_markdown(path)`
- `save_to_video(path)`

For document, OCR, and multi-page pipelines, use a directory as the save target. A single fixed file path can overwrite outputs from multiple pages or submodules.

## Parallel and multi-device inference

PaddleX supports device strings such as `cpu`, `gpu:0`, or `gpu:0,1,2,3` where the selected pipeline and installed backend support them. Multi-device inference is a runtime/device plan, not a different pipeline name.

Checklist:

- verify the installed PaddlePaddle build supports the requested hardware.
- set `device` explicitly instead of relying on auto-detection for reproducible runs.
- keep input batching modest before increasing parallelism.
- for HPI/TensorRT paths, route backend setup to `../deployment/`.

## Heavy or optional cases

Treat these as optional unless the environment is explicitly prepared:

- `PP-DocTranslation`: external chat-bot/LLM configuration and credentials.
- `PP-ChatOCRv4-doc`: multimodal/LLM backend and possibly remote service.
- `PaddleOCR-VL*`: large VLM models and GenAI client/server configuration.
- video pipelines: video decoder and codec stack.
- 3D BEV: dataset layout and 3D dependencies.
