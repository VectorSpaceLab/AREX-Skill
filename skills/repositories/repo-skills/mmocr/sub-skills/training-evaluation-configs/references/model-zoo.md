# Model zoo and config-family guide

MMOCR's model zoo is organized by task and family. Each family has official configs and checkpoints in the installed/source package distribution; use this page to match task, model family, config, evaluator, checkpoint, and optional AMP/TTA choices without reopening the original repository.

## Matching rules

1. Match the **task** first: text detection, text recognition, or KIE.
2. Match the **family** next: DBNet config with DBNet checkpoint, CRNN config with CRNN checkpoint, SDMGR config with SDMGR checkpoint, and so on.
3. Use `model.type` from the smoke helper as a sanity check, but do not rely on it alone: wrapper families such as Mask R-CNN may use a generic top-level type.
4. Check evaluator type: text detection uses H-mean/IoU-style metrics, recognition uses word/character/NED metrics, and KIE uses F1-style metrics.
5. Treat checkpoint URLs as network/cache operations; prefer caller-provided local checkpoint paths for deterministic runs.

## Text detection families

Text-detection configs normally evaluate with `HmeanIOUMetric` or a multi-dataset evaluator containing that metric.

| Family | Typical model type or clue | What to know | AMP status from docs |
|---|---|---|---|
| DBNet | `DBNet` | Common segmentation-style detector with ResNet-18/50 and DCNv2 variants on datasets such as ICDAR2015, TotalText, and SynthText. | Supported. |
| DBNet++ | DBNet-style collection/config name | DBNet++ collection with DBNet-style FPNC variants; match by family/checkpoint name as well as model type. | Supported. |
| DRRG | `DRRG` | Graph reasoning family for arbitrary-shape text. | Not supported; docs cite `roi_align_rotated` fp16 limitation. |
| FCENet | `FCENet` | Fourier contour embedding family with ResNet/DCNv2/OCLIP variants. | Not supported; docs cite `BCELoss` fp16 limitation. |
| Mask R-CNN | `MMDetWrapper` plus Mask R-CNN family clue | MMDetection wrapper collection for text detection; top-level type alone is not enough. | Supported. |
| PANet | `PANet` | Pixel aggregation network for curved/natural scene text datasets. | Supported. |
| PSENet | `PSENet` | Progressive scale expansion family. | Supported. |
| TextSnake | `TextSnake` | Arbitrary-shape text detector with FPN-UNet-style necks. | Not supported in the docs table. |

## Text recognition families

Recognition configs commonly evaluate with `WordMetric`, `CharMetric`, `OneMinusNEDMetric`, or `MultiDatasetsEvaluator`. Recognition is also the task route where test-time augmentation is documented.

| Family | Typical model type or clue | What to know | AMP/TTA notes |
|---|---|---|---|
| ABINet | `ABINet` | Vision/language recognition family. | AMP supported; TTA only when config defines TTA fields. |
| ASTER | `ASTER` | Rectification plus attention recognizer. | Present in the model zoo; verify before enabling AMP. |
| CRNN | `CRNN` | Lightweight CTC baseline. A verified smoke on a CRNN config returned `default_scope=mmocr`, `model.type=CRNN`, train batch size `64`, and test dataset `ConcatDataset`. | AMP supported. |
| MASTER | `MASTER` | Multi-aspect non-local recognizer. | AMP supported. |
| NRTR | `NRTR` | Sequence-to-sequence recognizer with modality-transform or ResNet31 variants. | AMP supported. |
| RobustScanner | `RobustScanner` | Position-aware recognizer. | AMP supported. |
| SAR | `SARNet` with SAR family clue | Show-attend-read family; match SAR collection/checkpoints despite `SARNet` type. | AMP supported. |
| SATRN | `SATRN` | 2D self-attention recognizer. | AMP supported. |
| SVTR | `SVTR` | Single visual model recognizer with tiny/small/base/large variants. | Present in model zoo; verify before enabling AMP. |

## KIE family

KIE configs pair with F1-style metrics and WildReceipt-style key/value layouts.

| Family | Typical model type or clue | What to know | AMP notes |
|---|---|---|---|
| SDMGR | `SDMGR` | Spatial dual-modality graph reasoning for receipt key information extraction; variants can include visual/no-visual and open-set behavior. | No AMP support claim found in inspected training docs; treat AMP as unverified. |

## Checkpoint/config compatibility checklist

Before testing or setting `load_from`:

- Task and family names match.
- `model.type` and wrapper clues are expected for that family.
- Recognition dictionary, number of classes, and head settings match the checkpoint.
- Dataset/evaluator task matches the checkpoint's task.
- Device/backend can run the operators used by that family.
- For AMP, the family is supported or the user explicitly accepts an experimental run.
- For TTA, the smoke helper reports `has_tta=true`.

## Choosing a minimal debug route

- For config editing: run the smoke helper only.
- For dataset integration: route to `data-preparation` and validate tiny annotations before training.
- For inference demos: route to `ocr-inference`; do not use train/test launchers for image-folder OCR.
- For component extension: route to `model-api-components` and verify registries/DataSamples before a full experiment.
