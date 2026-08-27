# quality-safety-governance Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output is blocked unexpectedly | A safety policy or anonymization rule fired. | Inspect the policy scope and narrow it before re-running. |
| Reflection never triggers | The reflection config is off or the workflow never reached the reflection hook. | Confirm the reflection arguments and the point where the hook should run. |
| Tracing is silent | The tracing provider or its optional backend is missing. | Install and configure the tracing backend before assuming the code path is wrong. |
| Prompt logging fails | The PromptLayer client or credential is not configured. | Re-check the PromptLayer setup and rerun the tiny smoke check. |
| A policy scope flag behaves strangely | Multiple policy destinations were enabled when the run expected one. | Revisit the task and agent policy-scoping flags first. |

## Smoke check

```bash
python sub-skills/quality-safety-governance/scripts/check_policy_imports.py
```
