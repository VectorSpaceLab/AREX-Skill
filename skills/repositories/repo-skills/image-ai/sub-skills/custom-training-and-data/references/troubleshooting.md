# Troubleshooting ImageAI Custom Training and Data

Use this matrix when validation, conversion, or trainer setup fails. The entries
reflect the current ImageAI 3.x PyTorch source path.

## Data layout problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `missing classification split directory` | Dataset uses `validation` instead of `test`, or split folders are nested one level too deep. | Rename/move to `<dataset>/train/<class>/...` and `<dataset>/test/<class>/...` for classification. |
| `no class directories found` | Images were placed directly under `train` or `test`. | Create one folder per class and move images into the matching class folder. |
| `empty class folder` | A class has no supported image files. | Add images or remove the class from both splits. |
| Train/test class mismatch | `test` lacks a class present in `train`, or includes an extra class. | Keep the same class folder names in both splits. |
| Detection loader sees no labels | Annotation stems do not match image stems, or annotations are not under `annotations`. | Use `train/images/name.jpg` with `train/annotations/name.txt`; repeat for `validation`. |
| Duplicate image stem | Files like `case.jpg` and `case.png` exist in one split. | Keep one image per stem so the derived annotation path is unambiguous. |
| Extra detection annotation | There is a `.txt` annotation without a matching image. | Add the missing image or remove/rename the annotation. |

## YOLO annotation problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `expected 5 YOLO columns` | A row is not `<class_id> x_center y_center width height`. | Rewrite the row with one integer class id and four normalized floats. |
| `class id must be a zero-based integer` | Label names or one-based ids were used in `.txt`. | Use `0` for the first class, `1` for the second, and so on. |
| Coordinates outside `[0, 1]` | Pixel coordinates were written instead of normalized YOLO coordinates, or box conversion failed. | Convert from pixels to normalized center-x, center-y, width, height relative to image size. |
| Width/height not positive | `xmax <= xmin`, `ymax <= ymin`, or a zero-area object. | Correct or remove the bad box. |
| Strict box-extents failure | Center and size values imply part of the box is outside the image. | Recompute coordinates or clip boxes during annotation cleanup. |
| Empty `.txt` warning | Negative image or missing objects. | Allowed only if intentional; otherwise annotate objects. |
| Missing labels for a class id | `classes.txt` contains a class that appears nowhere. | Add examples or remove/reindex the unused class before training. |

## Pascal VOC conversion problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `images without matching VOC XML annotations` | File stems differ, e.g. `img01.jpg` vs `image01.xml`. | Rename files so stems match exactly before conversion. |
| `VOC XML annotations without matching images` | Annotation file has no image pair. | Add the image or remove the orphan XML. |
| `missing <size>` or width/height errors | XML lacks valid image dimensions. | Add positive numeric `<width>` and `<height>` under `<size>`. |
| `missing <bndbox>` | An object entry has a label but no bounding box. | Add `xmin`, `ymin`, `xmax`, `ymax` under `<bndbox>`. |
| `bbox is outside image size` | VOC coordinates exceed the declared XML image size. | Fix the XML size or box coordinates. |
| Output directory already exists | Converter avoids overwriting non-empty outputs by default. | Choose a new `--output-dir` or pass `--overwrite` deliberately. |
| Wrong class order after conversion | Converter sorts class names alphabetically. | Use generated `classes.txt` order as `object_names_array`, or reindex all YOLO files consistently. |

## Trainer setup problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `expected a path to a directory` from classification `setDataDirectory` | Dataset root path is wrong. | Pass the dataset root containing `train` and `test`. |
| `The parameter passed should point to a valid directory` from detection `setDataDirectory` | Dataset root path is wrong. | Pass the dataset root containing `train` and `validation`. |
| `.h5` rejected | ImageAI 3.x uses PyTorch, not TensorFlow models. | Use `.pt`/`.pth` weights, or intentionally use ImageAI 2.1.6 with TensorFlow for old `.h5` assets outside this skill. |
| Invalid extension rejected | Transfer/pretrained model suffix is not `.pt` or `.pth`. | Provide a PyTorch checkpoint file. |
| Weight load errors or poor transfer | Transfer weights do not match selected architecture. | Match ResNet-to-ResNet, DenseNet-to-DenseNet, YOLO-to-YOLO, TinyYOLO-to-TinyYOLO. |
| Detection pretrained load falls back to random weights | The current detection loader catches incompatible state dicts and prints fallback text. | Check model type, file integrity, and class-count compatibility; expect slower convergence if random initialized. |
| CUDA out of memory | Batch size is too high or model is too large. | Lower `batch_size`, use TinyYOLOv3 for detection, or move to a larger GPU. |
| CPU training is extremely slow | No CUDA is available or environment is CPU-only. | Treat CPU as a smoke-check backend; use CUDA for real training. |
| Training tests are skipped or too expensive | Full tests require datasets and release/pretrained weights. | Run validators/converter as safe checks; run bounded training only when assets and budget are supplied. |

## Deprecated or stale parameter issues

The active ImageAI 3.x PyTorch APIs differ from older docs and stale examples.
If a user supplies one of these, correct it before running code:

| Stale item | Current 3.x replacement |
| --- | --- |
| `ClassificationModelTrainer.trainModel(num_objects=..., enhance_data=True, show_network_summary=True)` | `trainModel(num_experiments=..., batch_size=..., model_directory=None, transfer_from_model=None, verbose=True)` |
| Classification `loadModel(num_objects=...)` | Custom classification `loadModel()` with no arguments after setting model path and JSON path. |
| TensorFlow `.h5` custom or pretrained models | PyTorch `.pt` or `.pth` weights. |
| `classification_speed`, `detection_speed`, speed mode strings | Removed in current PyTorch loading path. |
| Pascal VOC as direct custom detection training format | Convert VOC XML to YOLO `.txt` first. |
| `DetectionModelTrainer.evaluateModel(...)` standalone mAP evaluation | Removed from current PyTorch custom detection trainer; training prints validation metrics during epochs. |
| `pycocotools` for custom YOLO training | Not used by the current PyTorch path covered here. |

## Metrics and model-behavior questions

- In single-class detection, a `class loss` value that remains `0.00000` can be
  normal because there is no multi-class discrimination term.
- Low or unstable mAP in early detection epochs is expected; inspect trends over
  epochs and data quality rather than a single first-epoch value.
- Classification best accuracy is measured on the `test` split. If `test` is
  tiny or leaks training images, the score is not a reliable generalization
  estimate.
- Detection checkpoints are saved when `mAP@0.5` improves. A `_last.pt` file is
  also written at the final epoch.
- If no best checkpoint appears, check validation labels, class ids, and whether
  the training loop completed.

## Artifact handoff mistakes

| Mistake | Why it fails | Correct handoff |
| --- | --- | --- |
| Pairing a detection checkpoint with a JSON from another run | JSON stores labels and generated anchors for that training run. | Keep `<dataset>/models/*.pt` with the matching `<dataset>/json/*_detection_config.json`. |
| Passing detection artifacts to custom classification | Classification expects classes JSON, not anchors/labels detection config. | Route `.pt` + `<dataset_name>_model_classes.json` to `classification-workflows`. |
| Passing classification artifacts to custom detection/video | Detection expects YOLO/TinyYOLO weights and detection config JSON. | Route detection `.pt` + `*_detection_config.json` to `object-detection-workflows` or `video-detection-workflows`. |
| Forgetting the model-type setter used during training | Architecture mismatch causes load errors. | Record YOLO vs TinyYOLO and ResNet vs DenseNet/Inception/MobileNet with the artifact paths. |
