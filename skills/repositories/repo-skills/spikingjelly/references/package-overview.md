# SpikingJelly Package Overview

## Public package surfaces

- `spikingjelly.activation_based`: activation-based SNN modeling, ANN2SNN conversion, model zoo, distributed vision, backend kernels, precision, memopt, op counting, and exchange helpers.
- `spikingjelly.datasets`: neuromorphic datasets, builders, transforms, and utilities.
- `spikingjelly.timing_based`: timing-based helpers such as `GaussianTuning` and `Tempotron`.
- `spikingjelly.visualizing`: spike, voltage, and feature-map visualization helpers.
- `spikingjelly.configure` and `spikingjelly.logger`: package-wide configuration and logging behavior.
- `spikingjelly.activation_based.model`: SpikingResNet, SEW-ResNet, Spikformer, and training helpers.
- `spikingjelly.activation_based.distributed`: bounded distributed vision training and topology metadata.

## Install baseline

- Python `>=3.11`
- PyTorch `>=2.6.0`
- Install `spikingjelly` after PyTorch.

Optional extras used by the selected workflows:

| Feature | Install |
| --- | --- |
| CuPy backend | `pip install cupy-cuda12x` or `pip install cupy-cuda11x` |
| Triton backend | `pip install triton>=3.3.1` |
| NIR exchange | `pip install nir nirtorch` |
| Lightning integration | `pip install lightning jsonargparse[signatures]` |
| Qwen2 / transformer ANN2SNN flows | `pip install transformers==5.13.0` |
| FP8 TorchAO path | `pip install torchao` |
| FP8 Transformer Engine path | `pip install "transformer-engine[pytorch]"` |
| Megatron Core scale-out | `pip install megatron-core==0.18.2` on Python `>=3.12` |

## Major runtime objects

- Core SNN: `neuron.IFNode`, `neuron.LIFNode`, `layer.Linear`, `functional.reset_net`, `functional.set_step_mode`
- Data: `datasets.DVS128Gesture`, `datasets.CIFAR10DVS`, `datasets.SpikingHeidelbergDigits`
- Conversion: `ann2snn.Converter`, `ann2snn.FXConverter`, `ann2snn.ModuleConverter`
- Training: `model.spiking_resnet18`, `model.sew_resnet34`, `model.spikformer_ti`, `model.train_classify.Trainer`
- Performance: `precision.PrecisionConfig`, `precision.prepare_model_for_precision`, `memopt.memory_optimization`, `op_counter.DispatchCounterMode`
- Exchange: `nir_exchange.export_to_nir`, `nir_exchange.import_from_nir`

## Current inspection baseline

This skill was generated from source version `2.0.0.dev1`. The current environment used for evidence included CUDA, CuPy, Triton, NIR, and transformers inspection for the selected scope; optional FP8 and Megatron paths remained explicitly optional unless a sub-skill says otherwise.
