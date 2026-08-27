# Root module summary

For detailed module development, read `../sub-skills/modules/`.

Use modules when the user works below the pipeline level: `create_model`, custom datasets, config-driven `check_dataset`, `train`, `evaluate`, `export`, `predict`, distributed training, or checkpoint conversion.

Common API:

```python
from paddlex import create_model
model = create_model("PP-LCNet_x1_0")
```

Common config pattern:

```bash
python sub-skills/modules/scripts/run_module_smoke.py --config module_config.yaml --mode check_dataset
python sub-skills/modules/scripts/run_module_smoke.py --config module_config.yaml --mode train
python sub-skills/modules/scripts/run_module_smoke.py --config module_config.yaml --mode evaluate
python sub-skills/modules/scripts/run_module_smoke.py --config module_config.yaml --mode export
```

Run dataset checking before training. Export trained checkpoints before deployment or Paddle2ONNX conversion.
