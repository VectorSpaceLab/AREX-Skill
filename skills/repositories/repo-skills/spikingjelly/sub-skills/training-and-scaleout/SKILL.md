---
name: training-and-scaleout
description: "Teach SpikingJelly model-zoo image classification, train_classify
  Trainer workflows, Spikformer and SEW-ResNet training, and bounded distributed
  vision topology guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Scale-Out

Use this sub-skill when the task is to build, train, adapt, or sanity-check SpikingJelly image-classification workflows from the model zoo, including legacy `train_classify.Trainer` recipes and the newer distributed vision configuration API.

## Route here for

- Model-zoo image classifiers in `spikingjelly.activation_based.model`, especially `spiking_resnet`, `sew_resnet`, `spikformer`, and adjacent VGG-style baselines.
- `spikingjelly.activation_based.model.train_classify.Trainer`: subclassing, CLI arguments, optimizer/scheduler hooks, time-axis preprocessing, and model-output readout.
- `spikingjelly.activation_based.model.train_imagenet_example.SResNetTrainer`-style ImageNet recipes.
- Spikformer image-classification workflows, including `spikformer_ti`, `spikformer_s`, `spikformer_cifar10`, input/output shapes, and training-readout conventions.
- SEW-ResNet workflows, including `sew_resnet18/34/50/...`, residual connection choices, multi-step execution, and classification readout.
- Bounded distributed vision guidance with `spikingjelly.activation_based.distributed.vision`: `TrainingConfig`, `SEWResNet34Config`, `SpikformerConfig`, `SpikformerCIFAR10Config`, `train_classification`, DDP/FSDP2, channel TP, PP, and synthetic configuration smokes.
- Public tensor-parallel building blocks: `ChannelShardConv1d/2d` and `ChannelShardBatchNorm1d/2d`.

## Do not handle here

- Neuromorphic dataset download, preprocessing, event/frame builders, ImageFolder layout debugging, or data transforms beyond the training-facing layout contract. Route to [datasets](../datasets/).
- General SNN state, `step_mode`, surrogate-gradient, neuron/layer semantics, monitors, or reset basics. Route to [core-snn](../core-snn/) unless the question is specifically a training-loop placement issue.
- ANN2SNN conversion, calibration, or converted-model readout. Route to [ann2snn](../ann2snn/).
- Low-level CUDA/CuPy/Triton kernel behavior, FP8/profiling, precision tuning, memory profiling, or throughput benchmarking internals. Route to [performance-and-analysis](../performance-and-analysis/).
- Deployment/exchange formats such as NIR, Lava, or Lynxi. Route to [deployment-exchange](../deployment-exchange/).
- Megatron Core / LLM scale-out as an actionable workflow in the current verified scope. Treat it as reference-only unless a future run explicitly prepares Python 3.12 plus Megatron Core.

## Operating workflow

1. Identify the training surface:
   - For quick single-node or legacy DDP image training, start with `train_classify.Trainer` and override the model/time-axis hooks.
   - For bounded multi-GPU vision topologies, start with `distributed.vision.TrainingConfig`.
   - For pure model-zoo construction or a custom training loop, instantiate the model family directly and own `functional.reset_net(model)` after each independent batch/window.
2. Normalize the image/time layout:
   - Static images use `[N, C, H, W]`.
   - Multi-step sequences use `[T, N, C, H, W]` internally.
   - `distributed.vision.TrainingConfig.input_layout="NTCHW"` means the DataLoader yields `[N, T, C, H, W]`, which the trainer converts to time-first.
3. Reduce classification output explicitly:
   - Spiking image models commonly return `[T, N, C]`; use `y.mean(0)` or the task-defined firing-rate reduction before `cross_entropy`.
   - Dense-style `[N, C]` outputs are already reduced.
4. Keep `train_classify.Trainer` and `distributed.vision` separate:
   - `Trainer` is the extensible torchvision-reference-style trainer.
   - `distributed.vision` owns DDP/FSDP2/channel-TP/PP topology contracts.
5. Use the bundled smoke script before diagnosing a large run. It checks config round-trips, invalid topology guards, model-builder forwards, PP boundary shapes, and the `Trainer` override contract without downloads.

## Bundled references

- [`references/training-recipes.md`](references/training-recipes.md): model-zoo, `Trainer`, Spikformer, and SEW-ResNet recipes.
- [`references/distributed-and-llm.md`](references/distributed-and-llm.md): distributed vision configs, topology constraints, tensor-parallel building blocks, custom builders, and reference-only LLM notes.
- [`references/troubleshooting.md`](references/troubleshooting.md): training and scale-out failure modes.

## Bundled script

- [`scripts/vision_training_config_smoke.py`](scripts/vision_training_config_smoke.py): safe no-download synthetic smoke for `Trainer`, `distributed.vision.TrainingConfig`, built-in vision builders, and PP shape checks. It does not launch distributed training.

## Evidence base

Consulted source files:

- `spikingjelly/activation_based/model/__init__.py`
- `spikingjelly/activation_based/model/train_classify.py`
- `spikingjelly/activation_based/model/train_imagenet_example.py`
- `spikingjelly/activation_based/model/spiking_resnet.py`
- `spikingjelly/activation_based/model/sew_resnet.py`
- `spikingjelly/activation_based/model/spikformer.py`
- `spikingjelly/activation_based/distributed/__init__.py`
- `spikingjelly/activation_based/distributed/vision/config.py`
- `spikingjelly/activation_based/distributed/vision/training.py`
- `spikingjelly/activation_based/distributed/vision/sew_resnet.py`
- `spikingjelly/activation_based/distributed/vision/spikformer.py`
- `spikingjelly/activation_based/distributed/tensor_parallel/channel.py`
- `spikingjelly/activation_based/distributed/llm/{config,planning,training}.py` as reference-only LLM evidence
- `benchmark/vision_distributed.py` as the source evidence for the repository's synthetic distributed vision entrypoint

Consulted docs:

- `docs/source/tutorials/en/train_large_scale_snn.rst`
- `docs/source/tutorials/en/spikformer.rst`
- `docs/source/tutorials/en/distributed_training.rst`
- `docs/source/APIs/spikingjelly.activation_based.model.rst`
- `docs/source/APIs/spikingjelly.activation_based.distributed.rst`
- `docs/source/changelog.rst`

Consulted tests:

- `test/activation_based/test_spikformer_model.py`
- `test/activation_based/test_distributed_vision.py`
- `test/activation_based/test_distributed_tensor_parallel.py`
- `test/activation_based/test_distributed_config.py`
- `test/activation_based/test_distributed_planning.py`
- `test/activation_based/test_distributed_training.py`
- `benchmark/test/test_snn_single_gpu_benchmark.py`

Verified live-signature evidence:

- `skills/tests/spikingjelly/reports/environment/repo_env_report.json` confirms the prepared inspection environment imports `spikingjelly.activation_based.distributed`, has `spikingjelly 2.0.0.dev1`, Python 3.11, CUDA/CuPy/Triton readiness for the selected repo scope, and does not prepare the optional Megatron Core stack.
- Live introspection in that environment confirmed the public constructor signatures captured in the bundled references for `Trainer`, Spikformer factories, SEW-ResNet factories, `distributed.vision` config objects, `train_classification`, and tensor-parallel modules.

## Known limits

- `distributed.vision.train_classification` requires CUDA/NCCL at runtime; the bundled smoke is intentionally CPU-safe and checks configuration/model-builder contracts without launching training.
- Megatron Core LLM training is not verified in the current Python 3.11 inspection environment. Do not present LLM scale-out as a ready workflow unless a future scope prepares Python 3.12 plus `spikingjelly[megatron]` and verifies it.
- This sub-skill is not a throughput-tuning guide. Use it to choose valid training surfaces and topology bounds, then route backend-performance questions away.
