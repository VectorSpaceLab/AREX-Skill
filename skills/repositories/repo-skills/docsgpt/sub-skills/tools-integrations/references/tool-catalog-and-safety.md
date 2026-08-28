# Tool Catalog and Safety

## Tool families

| Family | Examples | Main risk/prerequisite |
|---|---|---|
| search/read | DuckDuckGo, Brave, read webpage, internal search, wiki | network/data disclosure, API keys, SSRF, source authorization |
| external action | generic API, MCP, Telegram, ntfy, crypto data | credentials, rate limits, third-party mutation/privacy |
| persistence | memory, notes, todo list, scheduler | user scoping, repeated/headless actions, stored data |
| database | PostgreSQL tool | SQL privileges, injection, large results, mutation |
| files/code | Read Document, Code Executor, Artifact Generator | parser limits, untrusted code, sandbox isolation, artifact quotas |
| remote machine | Remote Device | command execution, device token, approval/denylist, audit |
| reasoning/internal | think, internal search | loop/budget control; not all are user-configurable |

## Defaults

`DEFAULT_CHAT_TOOLS` can include only tools that load without required config and are compatible with synthetic ids. The shipped default is:

```text
memory, read_webpage, scheduler
```

Per-user preferences can disable individual defaults. Agent-bound chats resolve the agent's exact tool set rather than automatically adding defaults. Headless runs drop scheduler.

Built-in picker tools use deterministic synthetic ids. Do not hard-code or invent ids in portable agent definitions; resolve by the deployment's management/API surface.

## Action metadata

A useful action exposes:

- unique, stable name;
- concise description stating when to use and what returns;
- JSON-like parameter schema with types, required fields and constraints;
- config requirements separate from model-filled arguments;
- side-effect and approval policy;
- sanitized output/error contract.

Vague descriptions make the model choose the wrong action. Marking secrets as LLM-filled leaks them into prompts; keep static credentials in protected config.

## Approval policy

Require approval for:

- writes/deletes or financial/account actions;
- shell/code/database commands;
- messages/notifications sent externally;
- uploads/downloads involving sensitive data;
- uncertain targets or parameters;
- retries without idempotency.

Auto-approval is reasonable only for narrow, read-only, bounded actions against approved endpoints with redacted output. Headless runs need a pre-authorized policy because no browser user may be present.

## Failure handling

Return explicit tool status and sanitized errors to the agent. Bound tool attempts. Never let the model retry a state-changing call simply because it received an ambiguous timeout; first check whether the remote side committed the action.
