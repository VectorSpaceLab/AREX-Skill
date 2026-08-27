# Inference and Evaluation Troubleshooting

## Missing weights

Symptoms: checkpointer errors, empty `MODEL.WEIGHTS`, or file-not-found. Provide a local checkpoint path or a valid Detectron2-compatible URL through `--opts MODEL.WEIGHTS ...`.

## Headless OpenCV failure

Symptoms: `cv2.imshow` or display backend errors. Always pass `--output`, or use a script that serializes predictions instead of opening a window. In containers, install headless OpenCV variants if GUI support is not needed.

## Device surprise

The source demo chooses CUDA when `torch.cuda.is_available()`. If the user asked for CPU, ensure `MODEL.DEVICE cpu` is applied after any auto-device assignment or patch the local demo.

## Wrong labels or class colors

Check `DATASETS.CLASS_NAMES`, `MODEL.YOLO.CLASSES`, and the checkpoint's trained class count. For custom data, class ids and config class count must match.

## No dataset metadata

If `MetadataCatalog.get(cfg.DATASETS.TEST[0])` fails or is empty, register the dataset first. For simple image demos, labels may still need a class-name list for readable visualization.

## LazyConfig demo `NameError: q`

The source `demo_lazyconfig.py` has a bare `q` at module scope, so even `--help` fails. Remove that line in the user's working copy or create a minimal LazyConfig predictor from the model instantiation pattern.

## Evaluation returns no metrics

Check that the evaluator matches the task (bbox versus segmentation), the validation dataset is non-empty, and `DATASETS.TEST` is set. For SparseInst-like outputs without `pred_boxes`, use the instance segmentation route with `COCOMaskEvaluator`.
