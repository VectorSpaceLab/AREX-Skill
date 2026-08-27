# Training Workflows

## RL training CLI

```bash
rllm train <benchmark> --agent <agent> --model <model> --backend <verl|tinker|fireworks>
```

Important options:

- Dataset selection: `--train-dataset`, `--train-split`, `--val-dataset`, `--val-split`, `--max-examples`.
- Agent/evaluator: `--agent`, `--evaluator`. If no evaluator is supplied, rLLM resolves catalog/dataset verifier metadata similarly to eval.
- Optimization: `--group-size`, `--batch-size`, `--lr`, `--lora-rank`, `--epochs`, `--max-steps`, `--val-freq`, `--save-freq`, `--project`, `--experiment`, `--output`, `--config`.
- Runtime: `--ui/--no-ui`, `--sandbox-backend`, `--sandbox-concurrency`, `--sampling-params`, `--temperature`, `--top-p`, `--max-tokens`.

`rllm.cli.train.build_train_config(...)` maps CLI flags into an OmegaConf config and merges optional YAML config overrides. CLI flags override the config file.

## SFT CLI

```bash
rllm sft <registered-dataset> --backend tinker --model <model>
rllm sft --train-file data.jsonl --val-file val.jsonl --backend verl --gpus 1
```

Provide either a registered dataset name or `--train-file`. Supported file inputs mirror the dataset loader: Parquet, JSONL, and JSON are typical SFT formats.

## Programmatic trainer pattern

```python
from rllm.trainer import AgentTrainer

trainer = AgentTrainer(
    config=cfg,
    backend="verl",  # or "tinker" / "fireworks"
    agent_flow=agent_flow,
    evaluator=evaluator,
    train_dataset=train_dataset,
    val_dataset=val_dataset,
)
trainer.train()
```

Use programmatic construction when custom data loading, custom hooks, custom workflow classes, or advanced algorithm configuration is needed. Keep `agent_flow` and `evaluator` protocol details in the evaluation sub-skill.

## SFT programmatic pattern

```python
from rllm.trainer.agent_sft_trainer import AgentSFTTrainer
from rllm.trainer.sft.spec import SFTSpec

spec = SFTSpec(train_dataset="my-dataset", model="Qwen/Qwen3.5-4B", backend="tinker")
trainer = AgentSFTTrainer(spec)
trainer.prepare()
trainer.train()
```

Validate message rows before running a backend. The SFT data contract expects each row to carry a chat-style `messages` list after loading/curation.

## Gateway-backed rollout flow

1. Trainer provisions or connects to the model gateway.
2. Gateway creates session URLs and applies sampling params.
3. AgentFlow uses the session URL as its OpenAI-compatible `base_url`.
4. Gateway traces are converted to rLLM `Step` payloads for training/eval enrichment.
5. Backend transforms episodes/trajectory groups into its native batch format.

Read root `../../../references/gateway-and-traces.md` before debugging trace/session behavior.
