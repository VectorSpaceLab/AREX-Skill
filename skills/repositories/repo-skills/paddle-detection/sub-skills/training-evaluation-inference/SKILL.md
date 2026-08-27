---
name: training-evaluation-inference
description: "Builds and troubleshoots PaddleDetection training, evaluation,
  repository inference, distributed launch, AMP, logging, and slim command
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training, Evaluation, and Repository Inference

Use this route when the task asks to train, fine-tune, resume, evaluate, run `infer` on images/directories, perform slice inference, use VisualDL/W&B, launch multi-GPU jobs, enable AMP/fleet, or connect config/data/weights to PaddleDetection repository tools.

## Safe command planning

1. Choose and summarize a config with the model-zoo/config route.
2. Validate the dataset route before training or evaluation.
3. Decide device and budget. CPU is fine for parser/config checks; serious training and many tutorials expect GPU.
4. Construct commands with [`scripts/build_train_eval_infer_command.py`](scripts/build_train_eval_infer_command.py). It only prints commands for a user-provided checkout; it does not train.
5. Start with `use_gpu=false` or `--device=CPU` for smoke checks, local weights, a tiny image, and `--save_results` only when needed.
6. Promote to GPU/distributed/AMP only after the CPU/import/config/data preflight passes.

## Common command shapes

```bash
python tools/train.py -c <config.yml> --eval -o use_gpu=true
python tools/eval.py -c <config.yml> -o weights=<model.pdparams> use_gpu=true
python tools/infer.py -c <config.yml> --infer_img=<image.jpg> --output_dir=<out> -o weights=<model.pdparams> use_gpu=false
python -m paddle.distributed.launch --gpus 0,1,2,3 tools/train.py -c <config.yml> --eval
```

Treat the source-checkout `tools/*.py` scripts as target repository entry points, not files from this generated skill. Use the bundled command builder and references for the decisions.

## References

- [`references/training-workflows.md`](references/training-workflows.md): fine-tuning, resume, distributed launch, logging, AMP/slim, and output expectations.
- [`references/cli-reference.md`](references/cli-reference.md): verified training/eval/infer flags and override behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md): errors for devices, data, weights, configs, metrics, and optional dependencies.
