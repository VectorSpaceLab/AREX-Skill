# Local Model and Engine Reference

This reference summarizes the standalone predictor surface that feeds the local OCR route.

## Shared wrapper behavior

Most model classes inherit the same public wrapper behavior:

- `predict()` returns a list.
- `predict_iter()` streams results.
- Common constructor fields include `model_name`, `model_dir`, `device`, `engine`, `engine_config`, `enable_hpi`, `use_tensorrt`, `precision`, `enable_mkldnn`, `mkldnn_cache_capacity`, `cpu_threads`, and `enable_cinn`.
- CLI subcommands share the same core argument family, then add model-specific flags such as image size, thresholds, or `topk`.

## Model families at a glance

| Class | Default model | CLI subcommand | Notes |
| --- | --- | --- | --- |
| `TextDetection` | `PP-OCRv6_medium_det` | `text_detection` | Text-box detection with threshold and input-shape options. |
| `TextRecognition` | `PP-OCRv6_medium_rec` | `text_recognition` | Text recognition with optional `input_shape`. |
| `DocImgOrientationClassification` | `PP-LCNet_x1_0_doc_ori` | `doc_img_orientation_classification` | Four-way page orientation classification. |
| `TextLineOrientationClassification` | `PP-LCNet_x0_25_textline_ori` | `textline_orientation_classification` | 0°/180° textline orientation classifier. |
| `TextImageUnwarping` | `UVDoc` | `text_image_unwarping` | Image rectification / unwarping. |
| `LayoutDetection` | `PP-DocLayout_plus-L` | `layout_detection` | Document layout detection with threshold and layout merge settings. |
| `FormulaRecognition` | `PP-FormulaNet_plus-M` | `formula_recognition` | Formula image to LaTeX-style output. |
| `ChartParsing` | `PP-Chart2Table` | `chart_parsing` | Chart-to-table parsing; input is a dict with an `image` field. |
| `DocVLM` | `PP-DocBee2-3B` | `doc_vlm` | Document VLM; input is a dict with `image` and `query`. |
| `TableClassification` | `PP-LCNet_x1_0_table_cls` | `table_classification` | Wired/wireless table type classifier. |
| `TableCellsDetection` | `RT-DETR-L_wired_table_cell_det` | `table_cells_detection` | Wired/wireless table cell detection. |
| `TableStructureRecognition` | `SLANet` | `table_structure_recognition` | HTML/table-structure output. |
| `SealTextDetection` | `PP-OCRv4_mobile_seal_det` | `seal_text_detection` | Seal/stamp text detection. |

## Common CLI flags

The installed CLI exposes shared flags such as:

- `--input`
- `--model_name`
- `--model_dir`
- `--device`
- `--engine`
- `--enable_hpi`
- `--use_tensorrt`
- `--precision`
- `--enable_mkldnn`
- `--mkldnn_cache_capacity`
- `--cpu_threads`
- `--enable_cinn`

Model-specific flags vary by class:

- text detection: `--limit_side_len`, `--limit_type`, `--thresh`, `--box_thresh`, `--unclip_ratio`
- text recognition: `--input_shape`
- classification: `--topk`
- detection/layout/table: `--img_size`, `--threshold`, `--layout_nms`, `--layout_unclip_ratio`, `--layout_merge_bboxes_mode`

## Engine guidance

The shared engine list is:

- `paddle`
- `paddle_static`
- `paddle_dynamic`
- `transformers`
- `onnxruntime`

General advice:

- Use the default Paddle engine first when you want the simplest local setup.
- Switch to a non-default engine only when the selected model and environment support it.
- Treat `device` and engine selection as separate decisions: a CPU import does not prove GPU or accelerator behavior.

## Common pitfalls

- Do not assume every language/model combination is available for every OCR version.
- Do not assume a model family is available just because the class imports successfully; the model may still need a downloaded weight bundle.
- Do not reuse a single image-oriented predictor for a document-pipeline workflow when the full structured output is required.
