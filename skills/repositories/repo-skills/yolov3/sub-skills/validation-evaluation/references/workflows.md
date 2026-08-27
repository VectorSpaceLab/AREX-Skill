# Validation and Evaluation Workflows

## Native validation after training

After a bounded train smoke has produced `runs/train/smoke/weights/best.pt`:

```bash
python val.py --imgsz 64 --batch-size 32 --weights runs/train/smoke/weights/best.pt --device cpu --project runs/val --name smoke --exist-ok
```

Build a command without running validation:

```bash
python sub-skills/validation-evaluation/scripts/yolov3_eval_command_builder.py --weights runs/train/smoke/weights/best.pt --imgsz 64 --batch-size 32 --device cpu --name smoke --exist-ok
```

## Official-weight validation

```bash
python val.py --weights yolov3-tiny.pt --data data/coco128.yaml --imgsz 640 --batch-size 32 --device cpu
```

This may download official weights and coco128 assets if absent.

## Task modes

`--task` can be:

- `val`: default validation split.
- `train` or `test`: use those dataset YAML splits.
- `speed`: profile inference speed.
- `study`: run size/speed/accuracy study.

## Output interpretation

The printed summary includes precision, recall, mAP at IoU 0.5, and mAP at IoU 0.5:0.95. With `--verbose`, per-class AP is printed. `--save-txt` writes prediction labels; `--save-conf` appends confidences. `--save-json` writes COCO JSON predictions and enables pycocotools evaluation when dependencies and COCO-style annotations are available.
