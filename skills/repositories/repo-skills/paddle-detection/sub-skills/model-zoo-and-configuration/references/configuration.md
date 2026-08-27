# Configuration Workflow

PaddleDetection configs are YAML files with recursive `_BASE_` inheritance. The top-level file wins over inherited values after merges. Common high-value fields are:

- `architecture`: registered model name such as `YOLOv3`, `FasterRCNN`, `MaskRCNN`, `PicoDet`, `FairMOT`, or a task-specific architecture.
- `metric`: `COCO`, `VOC`, `MOT`, `KeyPointTopDownCOCOEval`, and related evaluators.
- `num_classes`: must match the dataset labels and model head.
- `TrainDataset`, `EvalDataset`, `TestDataset`: dataset type, `dataset_dir`, image/annotation paths, and transforms.
- `TrainReader`, `EvalReader`, `TestReader`: batch size, worker count, sample transforms, image shape, and collate behavior.
- `weights`, `pretrain_weights`, `resume`, `save_dir`: initialization, resume, and output policy.
- `use_gpu`, `use_xpu`, `use_npu`, `use_mlu`, `use_gcu`, and related vendor flags: backend selection; verify the Paddle build before enabling.

The shared CLI parser accepts:

```text
-c/--config path/to/config.yml
-o key=value nested.key=value
```

Values are parsed with YAML semantics, so quote strings containing spaces or characters that YAML interprets. Examples for a user-provided checkout:

```bash
python tools/train.py -c configs/ppyoloe/ppyoloe_crn_s_300e_coco.yml \
  -o use_gpu=false num_classes=3 save_dir=output/custom
python tools/infer.py -c configs/yolov3/yolov3_darknet53_270e_coco.yml \
  -o use_gpu=false weights=/models/model.pdparams --infer_img=/data/example.jpg
```

The commands are source-checkout entry points; use the bundled command builder when you need a reproducible command without reopening repository documentation. Always inspect the merged config before running a long job.
