# Cloud Deployment Troubleshooting

## Symptom-to-fix map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `bentoml not logged in` | BentoCloud credentials are missing. | Run `bentoml cloud login` in a private shell. Do not paste tokens into shared logs. |
| `Cannot find cloud config.` | The BentoCloud config file is absent from the expected BentoML home. | Confirm `bentoml cloud current-context` works and that the user has logged in. |
| `Environment variable ... is required but not provided` | The selected Bento declares a required env and noninteractive mode cannot prompt. | Provide `--env NAME` when the shell has the value, or `--env NAME=value` only in private. |
| `No available instance type` | BentoCloud returned no target whose accelerators satisfy the Bento resource spec. | Pick a smaller model, pass an explicit instance type if known, or verify account capacity. |
| `Failed to get cloud instance types` | BentoCloud command failed or returned invalid JSON. | Check context, credentials, network, and BentoML CLI version. |
| Deployment command exposes a token | A literal `--env NAME=value` was printed or logged. | Replace the value with `--env NAME` after exporting it in the private shell, or redact the command before sharing. |

## Safe recovery order

1. Confirm `openllm deploy --help` renders.
2. Resolve the model with `model-repositories` before contacting cloud.
3. Confirm BentoCloud login/context in a private shell.
4. Plan the command with `scripts/plan_deploy_command.py` and check missing env names.
5. Only run the live deployment after credentials, env variables, and instance type are clear.

## When to stop

Do not run live deploy in an automated skill-validation context unless the user explicitly authorized cloud side effects and credentials are available.
