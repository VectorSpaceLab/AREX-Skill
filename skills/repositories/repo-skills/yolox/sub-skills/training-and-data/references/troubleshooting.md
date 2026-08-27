# YOLOX Training And Data Troubleshooting

## First-triage commands

```bash
python scripts/inspect_yolox_exp.py --name yolox-s --expected-format none
python scripts/inspect_yolox_exp.py --exp-file path/to/exp.py --check-data --expected-format coco
python -m yolox.tools.train --help
python -m yolox.tools.eval --help
```

## Failure matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `plz provide exp file or exp name` | Neither `-n` nor `-f` supplied. | Add a built-in `-n yolox-s` or custom `-f path/to/exp.py`. |
| `doesn't contains class named 'Exp'` | Custom file lacks class `Exp` or has import errors. | Define `class Exp(...)`; run the inspect helper with `--show-traceback`. |
| Override has no effect | `Exp.merge` only sets existing attributes or shell parsing changed values. | Use exact field names and quote tuples like `input_size '(416,416)'`. |
| Odd `opts` length | Trailing overrides are not key/value pairs. | Supply pairs such as `max_epoch 2 print_interval 1`. |
| Input size assertion/failure | `input_size` not divisible by 32. | Use sizes such as 416, 512, 640, 800. |
| COCO annotation missing | Wrong `YOLOX_DATADIR`, wrong `data_dir`, or wrong annotation filename. | Set `YOLOX_DATADIR` parent containing `COCO/` or set `self.data_dir` to the COCO root. |
| Image file not found | Annotation `file_name` entries do not match `train2017`/`val2017`, or VOC ids lack JPGs. | Regenerate annotations or move/symlink images into expected directories. |
| Class/category mismatch | `num_classes`, category ids, evaluator, and checkpoint head differ. | Set `num_classes` to dataset categories and train/fine-tune a matching head. |
| VOC split/XML errors | Missing `ImageSets/Main/*.txt`, XML files, or class names not in VOC mapping. | Create correct split files or provide custom class transform/evaluator. |
| Strange loss/no matches | Bad boxes, empty annotations, class ids out of range, or extreme image size. | Inspect labels; run assignment visualization on a small batch. |
| CUDA OOM | Batch/model/image/cache/assignment too large. | Reduce batch, image size, cache, labels, or model size; avoid `-o` on shared GPUs. |
| `--fp16` errors | Mixed precision requested without compatible CUDA. | Drop `--fp16` or fix accelerator runtime. |
| Distributed hang | Mismatched ranks/world size or unreachable `--dist-url`. | Use single-node defaults or supply a reachable TCP URL and unique ranks. |
| Cache stale/wrong | Disk cache reused after data changes. | Delete cache directories after changing images, annotations, or read logic. |
| Resume checkpoint fails | Fine-tune weights used with `--resume`, or Exp changed. | Use `-c` without `--resume` for pretrained/fine-tune weights; resume only matching YOLOX training checkpoints. |
| Eval AP zero | Wrong evaluator/classes/checkpoint, too-high confidence, or preprocessing mismatch. | Match Exp/checkpoint/data; try low `--conf 0.001`; consider `--legacy` for old weights. |
| W&B/MLflow failures | Optional package, credentials, service URI, or network missing. | Install optional logger packages and configure credentials/services, or use TensorBoard. |

## Debug order

1. Inspect the Exp and data paths without starting training.
2. Compare `num_classes`, model selector, and checkpoint source.
3. Run CLI `--help` in the target environment.
4. Start with one device, small batch, no cache, and short `max_epoch`/`eval_interval` overrides.
5. Add cache, distributed launch, loggers, and FP16 only after the simple run is healthy.
