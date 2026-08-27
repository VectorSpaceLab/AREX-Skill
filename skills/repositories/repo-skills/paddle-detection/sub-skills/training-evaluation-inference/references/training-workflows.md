# Training and Evaluation Workflows

## Fine-tuning pattern

A typical PaddleDetection fine-tune uses a model config, a matching dataset config, optional pretrained weights, and a controlled output directory.

```bash
python tools/train.py -c <config.yml> --eval \
  -o pretrain_weights=<pretrained-or-local> num_classes=<N> save_dir=<output-root> use_gpu=true
```

When class shapes differ, PaddleDetection can ignore incompatible pretrained parameters, but you must still update dataset labels, `num_classes`, and metric settings before judging results.

## Resume and checkpoints

Use `-r/--resume` for a checkpoint path when continuing interrupted training. Weights used for evaluation/inference/export are passed through config overrides, usually `-o weights=<path-or-url>`. Keep pretraining, resume checkpoints, and final weights conceptually separate.

## Evaluation

Evaluation requires a config, dataset annotation, and weights. Useful flags include `--output_eval`, `--json_eval`, `--classwise`, `--save_prediction_only`, `--amp`, and slice-inference options for small objects. `--json_eval` expects already-generated JSON results in the evaluation output directory.

## Inference

Repository inference accepts `--infer_img`, `--infer_dir`, optional `--infer_list`, `--output_dir`, visualization thresholds, `--save_results`, VisualDL image logging, and small-object slice/merge options. `--infer_img` has higher priority than `--infer_dir`.

## Distributed and logging

Single-node multi-GPU training can use `python -m paddle.distributed.launch --gpus ... tools/train.py ...`; multi-node training uses `fleetrun`/fleet options and a stable IP list. VisualDL uses `--use_vdl=true --vdl_log_dir=<dir>`. W&B logging is exposed by `--use_wandb` and config keys; it may require credentials.

## Compression and slim

Train/eval/infer/export scripts accept `--slim_config`. Slim configs cover pruning, quantization, distillation, OFA, and post-training quantization paths. Treat slimming as a workflow modifier: verify baseline config first, then verify the slim config and deployment/export compatibility.
