---
name: training-finetuning
description: "Create, inspect, adapt, and troubleshoot LLM Foundry pretraining
  and fine-tuning Composer YAMLs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LLM Foundry training-finetuning

Use this sub-skill when a task involves LLM Foundry training configuration, launch commands, YAML overrides, pretraining, supervised or instruction fine-tuning, domain adaptation, sequence-length adaptation, checkpointing, resumption, training callbacks/loggers/optimizers/schedulers, or bounded smoke runs.

## Start here

1. Identify the requested workflow:
   - pretraining or continued pretraining/domain adaptation with a `text` MDS loader;
   - supervised/instruction fine-tuning with a `finetuning` loader;
   - a CPU smoke run that should be tiny and local;
   - a GPU, multi-GPU, or multi-node scaling adaptation;
   - checkpoint save/load/autoresume, callback/logger, optimizer/scheduler, or run-stability troubleshooting.
2. Read [references/workflows.md](references/workflows.md) for command patterns, override syntax, CPU/GPU scaling, MDS data paths, and MCLI/platform adaptation.
3. Read [references/configuration-reference.md](references/configuration-reference.md) when creating or reviewing a training YAML. It maps required `TrainConfig` fields, common optional fields, dataloaders, model/tokenizer/optimizer/scheduler sections, evaluation hooks, FSDP/TP, precision, and batch-size fields.
4. Read [references/checkpointing-and-callbacks.md](references/checkpointing-and-callbacks.md) for save/load/autoresume, checkpoint naming, HF checkpoint callbacks, run monitors, loggers, optimizers, and schedulers.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when launch, data, tokenizer/model, optional dependency, memory, FSDP/TP, or checkpoint upload errors appear.
6. Before launching a long run, run the safe bundled probe:

```bash
python scripts/llmfoundry_config_probe.py <config.yaml> \
  variables.data_local=<data-local> \
  train_loader.dataset.split=train_small \
  max_duration=2ba
```

The probe only parses the YAML and override strings. It does not train, download models or data, initialize distributed state, or write checkpoints. Diagnostic flags such as `--json` or `--strict` may appear before or after the YAML path; OmegaConf overrides remain ordinary `key=value` tokens.

## Primary public CLI

Use the installed public CLI for package-level training:

```bash
llmfoundry train <config.yaml> [overrides...]
```

Examples:

```bash
llmfoundry train <pretrain.yaml> \
  variables.data_local=<data-local> \
  train_loader.dataset.split=train_small \
  eval_loader.dataset.split=val_small \
  max_duration=10ba \
  eval_interval=0 \
  save_folder=<save-folder>

llmfoundry train <sft.yaml> \
  train_loader.dataset.hf_kwargs.data_dir=<data-local> \
  train_loader.dataset.preprocessing_fn=<python.module>:<function> \
  max_duration=1ep
```

For multi-process training, the public command still represents the training entry point, but the cluster or launcher must start the required processes and provide distributed environment variables. Platform job YAMLs are reference-only adaptation material; do not copy account-, cluster-, or credential-specific values blindly.

## Boundaries

This sub-skill owns:

- Composer YAML creation and adaptation for pretraining, SFT/instruction tuning, domain adaptation, sequence-length adaptation, and small smoke runs.
- `TrainConfig` required/optional fields that affect training, evaluation hooks inside training, callbacks, algorithms, loggers, optimizer/scheduler, save/load/autoresume, precision, FSDP, TP, and batch sizing.
- Training launch commands and CLI override strings.
- Training-specific troubleshooting.

Route elsewhere:

- Data conversion schemas, prompt/response conversion tools, and MDS writing details: data-preparation.
- Standalone eval task schema, ICL task authoring, and Eval Gauntlet details: evaluation.
- Checkpoint export to HF/ONNX/FasterTransformer and text generation: inference-conversion.
- Model registry internals, MPT configuration depth, custom package registrations, and API extension design: package-apis-configuration.

## Safety rules

- Do not start an unbounded training run while inspecting a config. Probe first, then set explicit `max_duration`, `eval_interval`, `save_interval`, data split, and checkpoint destination.
- Do not use local source checkout paths in runtime instructions. Use placeholders such as `<config.yaml>`, `<data-local>`, `<data-remote>`, `<save-folder>`, `<load-checkpoint>`, `<hf-model>`, and `<run-name>`.
- Treat model and tokenizer downloads, gated Hugging Face models, object-store checkpoints, MCLI jobs, CUDA kernels, Flash Attention, TransformerEngine, and MegaBlocks as environment-dependent.
- Keep conversion and export out of this sub-skill even when a training checkpoint is the input or output of that later workflow.
