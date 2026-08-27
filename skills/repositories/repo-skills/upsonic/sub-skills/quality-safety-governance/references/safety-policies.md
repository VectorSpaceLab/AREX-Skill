# Safety Policies and Governance

## Main surfaces to know

| Surface | Use |
| --- | --- |
| `safety_engine` | Policy classes and anonymization helpers for content filtering and safe handling. |
| `Task.policy_apply_to_*` | Scope flags that tell the runtime which parts of a task should be policy-checked. |
| `Agent` policy args | `user_policy`, `agent_policy`, `tool_policy_pre`, `tool_policy_post`, and the feedback-loop controls. |
| `ToolConfig` | HITL flags, cache controls, and tool-output visibility knobs. |
| `PromptLayer` | Prompt management and execution logging integration. |
| `TracingProvider` / `DefaultTracingProvider` | OpenTelemetry-style tracing and observability support. |

## What to remember

- Route policy definitions here instead of burying them inside the agent runtime or tools route.
- Use this route when the user wants safe output handling, governance, or tracing behavior.
- Keep the policy reference focused on behavior and recovery, not on every individual policy class.
