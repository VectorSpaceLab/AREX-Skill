# Trainer API Reference

## Main imports

```python
from rllm.trainer import AgentTrainer
from rllm.trainer.backend_protocol import BackendProtocol
from rllm.cli.train import build_train_config
from rllm.trainer.agent_sft_trainer import AgentSFTTrainer
from rllm.trainer.sft.spec import SFTSpec
```

Validated signatures:

```python
AgentTrainer(
    config,
    workflow_class=None,
    train_dataset=None,
    val_dataset=None,
    workflow_args=None,
    backend="verl",
    agent_flow=None,
    evaluator=None,
    hooks=None,
    sandbox_backend=None,
    sandbox_concurrency=None,
    store=None,
    **kwargs,
)

build_train_config(
    *, model_name, group_size, batch_size, lr, lora_rank,
    total_epochs, total_steps, val_freq, save_freq,
    project, experiment, output_dir, config_file,
)
```

## Backend protocol

Backends implement setup, episode generation, backend-batch transformation, policy update, validation, checkpoint/save/sync lifecycle, and shutdown hooks. Use the concrete backends rather than reimplementing this protocol unless the user is adding a new backend.

## Algorithm config concepts

`rllm.trainer.algorithms.config.AlgorithmConfig` centralizes RL algorithm behavior:

- loss function names such as PPO/GRPO variants, DAPO, CISPO, and related aggregation modes;
- rollout correction, router replay, shared-key synchronization, filtering, and rejection sampling options;
- stepwise advantage mode and advantage estimator routing.

Advanced settings are backend-sensitive. Check `backend-matrix.md` and `troubleshooting.md` before changing them.

## SFT spec fields

`SFTSpec` captures dataset/file selection, backend, model, LoRA rank, learning rate, batch size, epochs/max length, tokenization/masking method, LR schedule, validation/save frequency, project/experiment, output directory, config overrides, and backend-specific launch options such as GPUs for Verl.

SFT backends convert this spec into backend templates:

- Tinker SFT builds a Tinker config and validates chat-message rows.
- Verl SFT writes backend config and launches through torchrun.
- Fireworks SFT subclasses Tinker SFT behavior for data preparation but provisions Fireworks training infrastructure and checkpointing.
