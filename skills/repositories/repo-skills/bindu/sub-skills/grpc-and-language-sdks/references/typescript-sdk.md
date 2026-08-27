# TypeScript SDK Reference

Developer-facing shape:

```typescript
import { bindufy, type ChatMessage, type HandlerResponse } from "@bindu/sdk";

await bindufy({
  author: "dev@example.com",
  name: "my-agent",
  deployment: { url: "http://localhost:3773", expose: true },
  skills: ["skills/question-answering"],
  coreAddress: "localhost:3774",
  callbackPort: 0,
}, async (messages: ChatMessage[]): Promise<string | HandlerResponse> => {
  return `Echo: ${messages.at(-1)?.content ?? ""}`;
});
```

Config fields: `author`, `name`, `deployment`, optional `description`, `version`, `skills`, `capabilities`, `kind`, `execution_cost`, `coreAddress`, `callbackPort`, `extra_metadata`, `debug_mode`, `telemetry`, and `num_history_sessions`.

Skill loading:

- String skill paths are resolved from the SDK process working directory.
- `skill.yaml` or `SKILL.md` content is read locally and sent to the core as raw content.
- Inline skill objects can set name, description, tags, input/output modes, version, and author.

Handler response mapping:

| TS result | Core result | Task effect |
|---|---|---|
| string | string | completed |
| `{content}` | string content | completed |
| `{state:"input-required", prompt}` | dict state/prompt | open input-required |
| `{state:"auth-required", prompt}` | dict state/prompt | open auth-required |

Cleanup: the SDK sends heartbeats while alive and shuts down the callback server on process signals. Stop stale SDK/core processes before retrying confusing registration failures.
