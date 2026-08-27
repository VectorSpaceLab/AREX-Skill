# Foundation model customization

Use this file when the task is about adapting a foundation model with the
specialized SageMaker Python SDK v3 trainers.

## Trainer families

- `SFTTrainer` for supervised fine-tuning
- `DPOTrainer` for preference optimization
- `RLVRTrainer` for reinforcement learning with verifiable rewards
- `RLAIFTrainer` for reinforcement learning with AI feedback
- `CPTTrainer` for continued pre-training on Nova models
- `MultiTurnRLTrainer` for agentic multi-turn reinforcement fine-tuning

## Import map

```python
from sagemaker.train import (
    SFTTrainer,
    DPOTrainer,
    RLVRTrainer,
    RLAIFTrainer,
    CPTTrainer,
    MultiTurnRLTrainer,
)
from sagemaker.core.training.configs import Compute as TrainingJobCompute, HyperPodCompute
from sagemaker.train.common import TrainingType, CustomizationTechnique
```

`TrainingJobCompute` is the `Compute` alias used by the package for serverful
training jobs. `HyperPodCompute` is the cluster-backed option.

## Compute policy

- `compute=None` means serverless compute.
- `TrainingJobCompute` / `Compute` means standard managed training.
- `HyperPodCompute` means HyperPod-backed training.
- `CPTTrainer` requires `HyperPodCompute`.
- `MultiTurnRLTrainer` uses `agent_env` and `AgentRFTJob` rather than the
  ordinary training-job compute path.

## Common trainer shape

Most trainer constructors use a combination of:

- `model`
- `training_dataset`
- `compute`
- `accept_eula`
- `role`
- `sagemaker_session`
- optional model- or recipe-specific arguments

The `training_dataset` can usually be a raw S3 URI or a `DataSet` asset from the
AI Registry.

## Validation-first workflow

1. Pick the trainer family that matches the alignment objective.
2. Select the compute mode: serverless, serverful, or HyperPod.
3. Supply `accept_eula=True` when the model is gated and the license requires it.
4. Run `train(dry_run=True)` before a real submission.
5. Use `show_metrics()` and `stream_logs()` after submission to inspect the run.

## Example sketch

```python
from sagemaker.train import SFTTrainer
from sagemaker.train.common import TrainingType

trainer = SFTTrainer(
    model="meta-textgeneration-llama-3-2-1b-instruct",
    training_type=TrainingType.LORA,
    training_dataset="s3://<bucket>/train.jsonl",
    accept_eula=True,
)

trainer.train(dry_run=True)
```

## Handoff rules

- For evaluation jobs and AI Registry assets, move to
  `evaluation-and-ai-registry.md`.
- For data mixing, recipes, and notifications, move to
  `recipes-data-mixing-notifications.md`.
- For deployment, use the serving sub-skill instead of expanding this file.
