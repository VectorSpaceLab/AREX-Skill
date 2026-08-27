# Cross-cutting troubleshooting

Use this reference to classify the failure, then route to the focused sub-skill.

## Import fails before the requested workflow starts

Common symptoms:

```text
FileNotFoundError: .../data/coco/coco_labels.txt
ModuleNotFoundError: No module named 'cv2'
ModuleNotFoundError: No module named 'torchvision'
```

Actions:

1. Read [installation-and-compatibility.md](installation-and-compatibility.md) for core and optional dependencies.
2. For COCO label-map failures, route to [data-training troubleshooting](../sub-skills/data-training/references/troubleshooting.md). The failure can affect VOC-looking imports because of eager COCO default construction.
3. Install only the dependency needed by the selected workflow; do not install notebook, webcam, Visdom, and COCO dependencies for a model-only inspection.
4. Run `scripts/smoke_imports.py` after any environment change.

## Model construction or inference fails

Route to [model-inference](../sub-skills/model-inference/SKILL.md) when the symptom mentions:

- `build_ssd` returning `None`.
- unsupported `phase` or `size`.
- `num_classes` or state-dict shape mismatches.
- prior, loc, or conf tensor shapes.
- `Legacy autograd function with non-static forward`.
- device/default tensor mismatches during forward.

Do not route these failures to evaluation first; `eval.py`, `test.py`, and demos all depend on the same test-phase detection layer.

## Dataset or training setup fails

Route to [data-training](../sub-skills/data-training/SKILL.md) when the symptom mentions:

- `VOCdevkit`, `VOC2007`, `VOC2012`, `ImageSets/Main`, annotations, JPEG images, or COCO JSON files.
- `vgg16_reducedfc.pth`, `--basenet`, checkpoint resume, or `weights/`.
- `train.py --help` argparse failures.
- `detection_collate`, empty targets, malformed boxes, or augmentation errors.
- Visdom or CUDA choices for training.

Use the data validator before launching a long run.

## Evaluation, test, or demo fails

Route to [evaluation-demos](../sub-skills/evaluation-demos/SKILL.md) when the symptom mentions:

- VOC mAP, AP, precision/recall, `det_test_<class>.txt`, `detections.pkl`, or `test1.txt`.
- `--confidence_threshold`, `--top_k`, `--visual_threshold`, `--trained_model`, or `--voc_root`.
- `demo/live.py`, webcam, OpenCV GUI, `imutils`, or Jupyter notebook requirements.

If the actual failure is model-forward compatibility, follow the evaluation troubleshooting reference back to `model-inference`.

## External resources and unsafe actions

Do not treat these as routine smoke checks:

- Dataset download scripts.
- Full VOC/COCO training.
- Full VOC mAP evaluation.
- Pretrained/base weight downloads.
- Webcam loops or GUI windows.
- Notebook execution.

They require user intent, adequate storage/time, and workflow-specific environment checks in a Researcher session.
