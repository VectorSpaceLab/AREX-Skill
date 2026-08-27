# Troubleshooting

This page covers training and scale-out failures for the SpikingJelly image-classification model zoo and distributed vision stack.

## Route out first

- Dataset download, frame/event preprocessing, ImageFolder layout, or transform bugs: [datasets](../../datasets/)
- Core SNN state, reset, surrogate, or shape semantics: [core-snn](../../core-snn/)
- ANN2SNN conversion or calibration: [ann2snn](../../ann2snn/)
- Kernel, profiling, or backend-performance issues: [performance-and-analysis](../../performance-and-analysis/)
- NIR / Lava / Lynxi deployment exchange: [deployment-exchange](../../deployment-exchange/)

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Trainer.load_model` raises `NotImplementedError` | `train_classify.Trainer` is a base class | Subclass `Trainer` and override `load_model` |
| `Trainer` loss or accuracy looks wrong for spiking outputs | The model returned `[T, N, C]` but the trainer never reduced time | Override `process_model_output` and reduce the time axis explicitly, usually with `y.mean(0)` |
| Batch size or time expansion is wrong in a custom trainer | `preprocess_train_sample` / `preprocess_test_sample` did not add the time dimension | Expand `[N, C, H, W]` to `[T, N, C, H, W]` before the model forward |
| `RuntimeError: Trying to backward through the graph a second time...` | Stateful modules were not reset between batches | Call `functional.reset_net(model)` after each independent batch or sequence |
| `TrainingConfig` rejects `batch_size` or `pipeline_microbatches` | The local batch is not divisible by the pipeline microbatch count | Make `batch_size % pipeline_microbatches == 0` |
| `TrainingConfig` rejects `world_size` | The requested TP × PP topology does not divide the available processes | Make `world_size % (tensor_parallel_size * pipeline_parallel_size) == 0` |
| `TrainingConfig` rejects `step_mode='s'` with PP | The built-in vision PP path expects multi-step execution | Use `step_mode='m'` for PP, or set `pipeline_parallel_size=1` |
| `TrainingConfig` rejects `fp16` with PP | Built-in vision PP currently supports `fp32` and `bf16` only | Switch to `bf16` or remove PP |
| `TrainingConfig` rejects `memopt_level > 0` with PP | The built-in builders disallow PP + memopt | Disable memopt or remove PP |
| `SpikformerConfig` rejects `step_mode='s'` | Spikformer is a native multi-step architecture | Use `step_mode='m'` |
| `SEWResNet34Config` rejects `in_channels != 3` | The built-in distributed SEW path is ImageNet-style RGB only | Keep the built-in config at 3 input channels |
| `SEWResNet34Config` rejects `tau <= 1.0` | The built-in LIF parameter is outside the supported range | Use `tau > 1.0` |
| `SpikformerBuilder` rejects ragged image dimensions under PP | The image size is not divisible by the patch size | Choose an image size divisible by the patch size (typically 16 for the ImageNet-style model, 4 for CIFAR-10) |
| `ChannelShardConv*` raises a divisibility error | The channel count is not divisible by the TP size | Pick an even split across TP ranks or reduce TP |
| `ChannelShardConv*` raises `groups != 1` | Grouped convolutions are not supported by the channel-shard wrappers | Keep the wrapped convolution ungrouped |
| `distributed.vision.train_classification` complains about validation size | The validation dataset length is not divisible by the required DP factor | Make the validation split evenly divisible before launching the run |
| `distributed.vision` import works but training fails immediately on CPU | The runtime requires CUDA/NCCL | Use the bundled smoke script for CPU-only contract checks |
| `distributed.llm` import or training complains about Megatron Core | The optional Megatron stack is not prepared | Treat LLM scale-out as reference-only in this scope |
| `dataset_builder`, `optimizer`, `loss_function`, or `scheduler` cannot be imported | The config strings are not full import paths | Use importable module paths such as `package.module.function` |
| `Trainer` CLI works but the model never learns | The output reduction or preprocessing hooks do not match the model family | Check `preprocess_*`, `process_model_output`, and `functional.set_step_mode` together |

## Quick checks

### Confirm the legacy trainer surface

```bash
python - <<'PY'
from spikingjelly.activation_based.model.train_classify import Trainer
trainer = Trainer()
parser = trainer.get_args_parser(add_help=False)
args = parser.parse_args([])
print(args.model, args.epochs, args.batch_size)
PY
```

### Confirm the distributed vision config round-trip and builder shapes

```bash
python skills/disco/spikingjelly/sub-skills/training-and-scaleout/scripts/vision_training_config_smoke.py --case all --device cpu
```

### Confirm the model-zoo readout shape on a tiny synthetic batch

```bash
python - <<'PY'
import torch
from spikingjelly.activation_based import functional
from spikingjelly.activation_based.model import spikformer, sew_resnet

sew = sew_resnet.sew_resnet34(num_classes=5, step_mode='m')
functional.set_step_mode(sew, 'm')
functional.reset_net(sew)
print(tuple(sew(torch.randn(2, 1, 3, 32, 32)).shape))

spk = spikformer.spikformer_cifar10(T=1, num_classes=10)
functional.reset_net(spk)
print(tuple(spk(torch.randn(1, 3, 32, 32)).shape))
PY
```

## Evidence anchors

Primary evidence used for these troubleshooting rules:

- `spikingjelly/activation_based/model/train_classify.py`
- `spikingjelly/activation_based/model/train_imagenet_example.py`
- `spikingjelly/activation_based/model/spiking_resnet.py`
- `spikingjelly/activation_based/model/sew_resnet.py`
- `spikingjelly/activation_based/model/spikformer.py`
- `spikingjelly/activation_based/distributed/vision/config.py`
- `spikingjelly/activation_based/distributed/vision/training.py`
- `spikingjelly/activation_based/distributed/vision/sew_resnet.py`
- `spikingjelly/activation_based/distributed/vision/spikformer.py`
- `spikingjelly/activation_based/distributed/tensor_parallel/channel.py`
- `spikingjelly/activation_based/distributed/llm/{config,planning,training}.py`
- `test/activation_based/test_distributed_vision.py`
- `test/activation_based/test_distributed_tensor_parallel.py`
- `test/activation_based/test_spikformer_model.py`
- `skills/tests/spikingjelly/reports/environment/repo_env_report.json`

## Known limits

- This page does not attempt to debug dataset acquisition or file layout problems.
- It does not cover low-level kernel tuning, compiler flags, FP8 issues, or throughput profiling.
- Megatron Core issues remain out of scope unless a future verified environment prepares that stack.
