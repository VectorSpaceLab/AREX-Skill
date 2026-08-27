# Reliability, Reflection, and Evaluation

## Verified reflection surfaces

- `ReflectionConfig`, `ReflectionResult`, `ReflectionState`, and `ReflectionProcessor` live in the reflection subsystem.
- `ReliabilityProcessor` lives in the reliability layer and coordinates quality-improvement behavior.
- `eval` and tracing integrations are part of the same governance story when the user asks about post-run review or observability.

## Workflow guidance

1. Decide whether the issue is policy, reflection, reliability, or observability.
2. Check the narrowest mechanism first.
3. Keep the verification path small and deterministic.
4. Only escalate to live provider or tracing backends when the workflow explicitly needs them.

## Good questions for future agents

- Was the output blocked because of a policy, or was it merely improved?
- Is the user asking for a retry / reflection loop, or for auditability and trace capture?
- Does the task need post-run scoring, logging, or an intervention point?
