# `wren ask` Prompt Shaping

## When to read

Read this when a workflow needs a Wren-aware prompt for another agent but should
not execute a database query itself.

## Commands

```bash
wren ask "user request" --guided
wren ask "user request" --direct
```

Exactly one flag is required. Supplying neither or both is an error because the
two modes intentionally produce different prompts.

## Mode selection

| Mode | Use when |
| --- | --- |
| `--guided` | The receiving agent needs a strict task flow and explicit sequencing |
| `--direct` | The receiving agent is capable and should receive minimal wrapping |

The command only renders a bundled template around the user prompt. It does not
inspect a project, retrieve memory, plan SQL, or contact a datasource. Route
those operations to the appropriate Wren workflow after the receiving agent
gets the prompt.

## Recovery

If the command reports an invalid mode, choose one of the two explicit flags.
If `wren` itself is missing, install the base package before treating prompt
shaping as available.
