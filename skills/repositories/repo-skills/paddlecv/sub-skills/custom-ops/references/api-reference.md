# API reference

## Registry and factory APIs

### `ppcv.core.workspace.register(cls)`
- Decorator that registers a class under its Python class name.
- The class name must be unique.

### `ppcv.core.workspace.create(cls_name, op_cfg, env_cfg)`
- Instantiates a registered class by name.
- Useful when a graph or config needs to create an op dynamically.

### `ppcv.core.workspace.get_global_op()`
- Returns the registry dictionary of all registered operator classes.

### `ppcv.ops.base.create_operators(params, mod)`
- Creates operator instances from a YAML list.
- `params` must be a list of operator descriptors.
- `mod` must export the class names used in the list.

## Base-class contract

| Base class | What it owns | Typical responsibility |
| --- | --- | --- |
| `BaseOp` | shared input filtering and validation helpers | common graph plumbing |
| `ModelBaseOp` | model loading, predictor setup, and batch inference | preprocess / infer / postprocess |
| `ConnectorBaseOp` | graph-to-graph transformations | crop, rotate, match, track, or compose intermediate data |
| `OutputBaseOp` | final rendering and saving | result formatting, visualization, JSON export |

## Common model operators
- `ClassificationOp` → `class_ids`, `scores`, `label_names`
- `DetectionOp` → `dt_bboxes`, `dt_scores`, `dt_class_ids`, `dt_cls_names`
- `SegmentationOp` → `seg_map`
- `FeatureExtractionOp` → `dt_bboxes`, `feature`, `rec_score`, `rec_doc`
- `KeypointOp` → `keypoints`, `kpt_scores`
- `OcrDbDetOp` → `dt_polys`, `dt_scores`
- `OcrCrnnRecOp` → `rec_text`, `rec_score`
- `PPStructureTableStructureOp` → `structures`, `dt_bboxes`, `scores`
- `PPStructureKieSerOp` → `pred_id`, `pred`, `dt_polys`, `rec_text`, `inputs`
- `PPStructureKieReOp` → `head`, `tail`
- `PPStructureResultConcatOp` → `dt_polys`, `rec_text`, `dt_bboxes`, `html`, `cell_bbox`, `structures`
- `SentimentAnalysisOp` → `label`
- `InformationExtractionOp` → `text`, `type`
- `TTSOp` → `fn`

## Common connector operators
- `ClsCorrectionOp`
- `BboxCropOp`
- `PolyCropOp`
- `FragmentCompositionOp`
- `KeyFrameExtractionOp`
- `TableMatcherOp`
- `PPStructureFilterOp`
- `PPStructureResultConcatOp`
- `OCRRotateOp`
- `TrackerOP`
- `BboxExpandCropOp`

## Common output operators
- `ClasOutput`
- `DetOutput`
- `FeatureOutput`
- `KptOutput`
- `SegOutput`
- `HumanSegOutput`
- `MattingOutput`
- `OCROutput`
- `OCRTableOutput`
- `PPStructureOutput`
- `PPStructureSerOutput`
- `PPStructureReOutput`
- `TrackerOutput`

## Graph contract reminders
- `Inputs` must refer to an earlier output key using `{last_op}.{output_name}` syntax.
- The first op usually reads from `input.image`, `input.video`, or another `input.*` key.
- A custom op must keep its returned keys aligned with `get_output_keys()`.
- The class name used in the YAML must match the registered Python class name exactly.
