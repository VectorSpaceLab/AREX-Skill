# Task catalog

## How to choose
- Use `task_name` when the request matches one of the built-in `TASK_DICT` entries.
- Use `config_path` when the user wants a specific DAG, a unittest config, or a custom operator graph.
- Use the owning sub-skill to decide whether the task is single-op, system-pipeline, or custom-op work.

## Built-in task names (`PaddleCV(task_name=...)`)

### Single-model presets
| Task name | Typical workflow | Owner |
| --- | --- | --- |
| `PP-LCNet` | image classification | `single-model-inference` |
| `PP-LCNetV2` | image classification | `single-model-inference` |
| `PP-HGNet` | image classification | `single-model-inference` |
| `PP-YOLO` | object detection | `single-model-inference` |
| `PP-YOLOv2` | object detection | `single-model-inference` |
| `PP-YOLOE` | object detection | `single-model-inference` |
| `PP-YOLOE+` | object detection | `single-model-inference` |
| `PP-PicoDet` | lightweight detection | `single-model-inference` |
| `PP-HumanSegV2` | human segmentation | `single-model-inference` |
| `PP-LiteSeg` | semantic segmentation | `single-model-inference` |
| `PP-MattingV1` | matting / alpha mask | `single-model-inference` |

### System presets
| Task name | Typical workflow | Owner |
| --- | --- | --- |
| `PP-OCRv2` | OCR pipeline | `system-pipelines` |
| `PP-OCRv3` | OCR pipeline | `system-pipelines` |
| `PP-OCRv3-IE` | OCR + information extraction | `system-pipelines` |
| `PP-OCRv3-SA` | OCR + sentiment analysis | `system-pipelines` |
| `PP-OCRv3-TTS` | OCR + text-to-speech | `system-pipelines` |
| `PP-Structure` | layout / table / OCR structure pipeline | `system-pipelines` |
| `PP-ShiTu` | image retrieval / recognition | `system-pipelines` |
| `PP-ShiTuV2` | image retrieval / recognition | `system-pipelines` |
| `PP-Human` | human analysis pipeline | `system-pipelines` |
| `PP-Human-Attr` | human attribute analysis | `system-pipelines` |
| `PP-Vehicle` | vehicle analysis pipeline | `system-pipelines` |
| `PP-Vehicle-Attr` | vehicle attribute analysis | `system-pipelines` |
| `PP-TinyPose` | pose estimation pipeline | `system-pipelines` |
| `Face-Detection-Attr` | face detection + attributes | `system-pipelines` |

## Direct config families (`Pipeline(config_path=...)`)

### Single-op configs
- `paddlecv/configs/single_op/PP-LCNet.yml`
- `paddlecv/configs/single_op/PP-LCNetV2.yml`
- `paddlecv/configs/single_op/PP-HGNet.yml`
- `paddlecv/configs/single_op/PP-YOLO.yml`
- `paddlecv/configs/single_op/PP-YOLOv2.yml`
- `paddlecv/configs/single_op/PP-YOLOE.yml`
- `paddlecv/configs/single_op/PP-YOLOE+.yml`
- `paddlecv/configs/single_op/PP-PicoDet.yml`
- `paddlecv/configs/single_op/PP-HumanSegV2.yml`
- `paddlecv/configs/single_op/PP-LiteSeg.yml`
- `paddlecv/configs/single_op/PP-MattingV1.yml`

### System DAG configs
- `paddlecv/configs/system/PP-OCRv2.yml`
- `paddlecv/configs/system/PP-OCRv3.yml`
- `paddlecv/configs/system/PP-OCRv3-IE.yml`
- `paddlecv/configs/system/PP-OCRv3-SA.yml`
- `paddlecv/configs/system/PP-OCRv3-TTS.yml`
- `paddlecv/configs/system/PP-Structure.yml`
- `paddlecv/configs/system/PP-Structure-table.yml`
- `paddlecv/configs/system/PP-Structure-layout-table.yml`
- `paddlecv/configs/system/PP-Structure-ser.yml`
- `paddlecv/configs/system/PP-Structure-re.yml`
- `paddlecv/configs/system/PP-ShiTu.yml`
- `paddlecv/configs/system/PP-ShiTuV2.yml`
- `paddlecv/configs/system/PP-Human.yml`
- `paddlecv/configs/system/PP-Human-Attr.yml`
- `paddlecv/configs/system/PP-Vehicle.yml`
- `paddlecv/configs/system/PP-Vehicle-Attr.yml`
- `paddlecv/configs/system/PP-TinyPose.yml`
- `paddlecv/configs/system/Face-Detection-Attr.yml`

### Native tests that teach graph behavior
- `paddlecv/tests/test_pipeline.py` — end-to-end pipeline wiring.
- `paddlecv/tests/test_get_model.py` / `paddlecv/tests/test_list_model.py` — model catalog and path resolution smoke tests.
- `paddlecv/tests/test_detection.py`, `paddlecv/tests/test_segmentation.py`, `paddlecv/tests/test_feature_extraction.py`, `paddlecv/tests/test_keypoint.py` — actual single-op operator wiring tests.
- `paddlecv/tests/test_custom_op.py` plus `paddlecv/configs/unittest/test_cls_connector.yml`, `test_bbox_crop.yml`, `test_poly_crop.yml`, `test_fragment_composition.yml`, `test_key_frame_extraction.yml`, `test_table_matcher.yml`, `test_ppstructure_filter.yml`, `test_ppstructure_result_concat.yml` — extension and connector behavior.
- `paddlecv/tests/test_ocr.py` plus `paddlecv/configs/unittest/test_ocr_db_det.yml`, `test_ocr_crnn_rec.yml`, `test_ocr_layout.yml`, `test_ocr_table_structure.yml`, `test_seg_pphumansegv2.yml`, `test_seg_ppmattingv1.yml` — OCR and extra pipeline behavior.

## Notes
- The `TASK_DICT` list is smaller than the full direct-config catalog. If the user names a config path that is not in `TASK_DICT`, that is still a valid `Pipeline(config_path=...)` route.
- `PaddleCV` routes through `TASK_DICT` and handles the packaged task presets; the direct config route is for exact DAG control.
