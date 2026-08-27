# Classification workflows

These are bounded operating procedures. Do not download data/checkpoints or
launch full training as a smoke.

## Install and import

Use a private environment with PaddlePaddle, `yacs==0.1.8`, `pyyaml`, and
Pillow. The inspected environment uses PaddlePaddle GPU 2.6.2 on an A100; the
checkout documents older Paddle APIs, so verify each selected family.

PaddleViT has no installable package. Run a selected folder as its own source
root so bare imports resolve consistently:

```bash
cd /path/to/PaddleViT/image_classification/ViT
python -c 'import config, vit; print(config.__file__, vit.__file__)'
```

Never put two model directories first on one import path. For a parent process,
insert only the selected absolute folder at `sys.path[0]` in a fresh process.

The bundled scripts are intentionally different: they are standalone and do
not import this checkout. Run them from any directory:

```bash
python /path/to/skill/scripts/check_classification_config.py \
  --config /path/to/PaddleViT/image_classification/ViT/configs/vit_tiny_patch16_224.yaml
python /path/to/skill/scripts/classification_model_smoke.py --device cpu
```

## Build and inspect

1. Select one folder and its own README, `config.py`, model module, datasets,
   and YAML.
2. Validate YAML with the config checker.
3. In the selected folder, load `get_config`, call the documented builder, and
   run one synthetic `[B, C, H, W]` tensor. Default ViT is expected to produce
   `[1, 1000]`; this is not coverage for every model.
4. Attach real data/checkpoints only after imports, geometry, and one forward
   pass work.

## Evaluate, train, and finetune

Use the selected folder's main script and README. Typical common arguments are
`-cfg`, `-dataset`, `-data_path`, `-batch_size`, `-batch_size_eval`, `-eval`,
`-pretrained`, `-resume`, and `-amp`; inspect that folder's `--help` because
some families use distillation/EMA-specific mains. Batch size is per GPU.

For finetuning, use `-pretrained`, change `MODEL.NUM_CLASSES` deliberately,
and verify classifier-head compatibility. Use `-resume` only when restoring
optimizer/scheduler/epoch/scaler state is intended. Run one GPU and FP32 first;
then enable AMP and finally distributed execution.

## Facial expression

Use `facial_expression/` with `-dataset=ABAW`, `-data_folder`, `-anno_folder`,
and `-class_type=all|coarse|negative`. Confirm aligned 224x224 frames,
annotation `Train_Set`/`Validation_Set`, and the 8/5/4 class mapping before
using the Swin script.
