# Evaluation and Benchmarking

## Evaluation route

Prefer the training launcher with `--eval-only` over ad-hoc evaluation scripts because it uses the same config, model, checkpointer, dataset registration, and evaluator route as training.

Standard detection:

```bash
python train_det.py --config-file path/to/config.yaml --eval-only MODEL.WEIGHTS path/to/model.pth
```

SparseInst / instance segmentation:

```bash
python train_inseg.py --config-file path/to/sparseinst.yaml --eval-only MODEL.WEIGHTS path/to/model.pth
```

DETR-family:

```bash
python train_transformer.py --config-file path/to/detr.yaml --eval-only MODEL.WEIGHTS path/to/model.pth
```

## Dataset prerequisites

- `DATASETS.TEST` must name a registered validation dataset.
- The validation JSON and image root must exist.
- For custom datasets, register the validation split before building the trainer.
- For mask-only models, use the SparseInst/instance route so `COCOMaskEvaluator` can handle instances without boxes.

## Benchmarking

The source benchmark pattern repeats inference many times on one image and prints total/average time and input shapes. Use it only when the user asks for performance measurement and has specified hardware, model, config, checkpoint, image, warmup/repetition policy, and whether CUDA synchronization is needed.

Do not compare benchmark numbers across different devices, image sizes, or checkpoint/config combinations.

## Common expected outputs

- Detectron2 evaluation returns metric dictionaries and writes inference artifacts under the configured output directory.
- Benchmark outputs include total time, average time, transformed input shape, and original image shape.
