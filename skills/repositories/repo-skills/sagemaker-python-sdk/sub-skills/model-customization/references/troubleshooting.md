# Model customization troubleshooting

Use this file when a foundation-model customization or evaluation flow fails.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `dry_run=True` fails | invalid config, dataset path, role, or recipe layer | fix the validation error before submitting a job |
| `ValueError` about percentages | Nova data-mixing percentages do not sum to 100 | correct the `DataMixingConfig` values |
| CPT configuration rejected | compute is not HyperPod | use `HyperPodCompute` for CPT |
| Multi-turn RL setup fails | `agent_env` is invalid or incomplete | supply a valid Bedrock AgentCore ARN, Lambda ARN, runtime ID, or `CustomAgentLambda` |
| notifications do not arrive | SNS policy or EventBridge permissions are missing | fix the SNS topic policy and IAM permissions |
| evaluator creation fails | missing dataset, role, or region | verify the registry asset inputs and credentials |
| metrics are empty | the job has not emitted them yet or the backend is mismatched | wait for the job to progress and confirm the backend type |

## Safe debugging sequence

1. Check the region and credentials.
2. Run `dry_run=True` on the trainer or evaluator.
3. Verify model access and EULA acceptance when the model is gated.
4. Inspect the resolved recipe before launch.
5. Confirm the compute type matches the selected trainer family.

## Model-specific reminders

- `CPTTrainer` is HyperPod-only.
- `MultiTurnRLTrainer` uses `agent_env` instead of ordinary training-job setup.
- `DataMixingConfig` is only meaningful for Nova data mixing flows.
- Notifications are supported for SMTJ, not HyperPod.

## Escalation

If the issue is really about ordinary training, deployment, or low-level
resources, hand the task to the sibling sub-skill instead of expanding this
file.
