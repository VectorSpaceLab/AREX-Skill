# Agent and Workflow Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| wrong agent behavior for type `react` | legacy alias maps to classic | select `agentic` or `research` explicitly when those semantics are needed |
| source context absent | source not attached/allowed, exposure mismatch, chunks zero, retrieval failure | inspect resolved agent config and retrieval trace |
| tool never selected | description/schema unclear, tool disabled, model lacks tool support | validate action metadata, model capability and prompt |
| tool loops indefinitely | weak stop condition or repeated error | bound tool/request count; surface errors; require terminal criteria |
| workflow save rejects `{{x}}` | braces used in CEL state/condition expression | change to bare CEL `x`; reserve braces for templates |
| workflow always takes else | case expression error or missing predecessor state | inspect state deltas and expression identifiers; ensure writer precedes reader |
| branch never finishes | missing end path or unbounded cycle | run offline graph validator; add counter/termination and end edge |
| node output missing | wrong generated key or output variable | standardize named outputs and verify predecessor completion |
| file input unsupported | forced native MIME/model mismatch | use `auto` or `extract`; verify parsing worker and limits |
| schedule/webhook task pending | Celery/Redis/queue failure | inspect task state and worker queues; do not retrigger without idempotency |
| headless run waits/fails on tool | tool requires user approval/device/OAuth/UI | remove it or provide an explicit headless-safe policy |
| import plan has unresolved items | target lacks source/tool/prompt/model; secrets were stripped | resolve plan, create as draft, re-enter credentials and retest |
| workflow export returns 400 | workflow agents are unsupported by portability endpoint | document/recreate graph separately; do not bypass validation |

Capture agent id/type/revision, model id, source/tool ids, workflow run/step, state delta, task id and sanitized error. Never log prompts or tool inputs containing secrets without an approved redaction policy.
