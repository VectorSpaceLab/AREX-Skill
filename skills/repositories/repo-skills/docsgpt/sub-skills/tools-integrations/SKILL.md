---
name: tools-integrations
description: "Guides DocsGPT built-in and API tools, MCP, approvals, artifacts and code execution, sandbox backends, remote devices, widgets, and webhooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tools and Integrations

Use this sub-skill to select/configure tools, import an API specification, connect MCP, enable artifact/code/document workflows, pair a remote device, or embed DocsGPT in another product.

## Route by task

- **Choose built-in tools and approval policy**: read [tool catalog and safety](references/tool-catalog-and-safety.md).
- **Generic REST API or MCP server**: read [API and MCP tools](references/api-and-mcp-tools.md), then validate the spec offline.
- **Artifacts, Code Executor, Read Document, Jupyter/Daytona sandbox, remote device**: read [sandbox, artifacts, and remote device](references/sandbox-artifacts-remote-device.md).
- **React/HTML widget, Chatwoot, agent webhook**: read [widgets and webhooks](references/widgets-webhooks.md).
- **Connection, auth, approval, rendering, device or schema failure**: read [troubleshooting](references/troubleshooting.md).

## Tool selection workflow

1. Define the action, data leaving DocsGPT, side effects, and required credentials.
2. Prefer a narrow built-in tool or generic API action over arbitrary code.
3. Describe each action/parameter so the model knows when and how to call it.
4. Validate schema and URL without execution.
5. Configure credentials through protected settings; never in prompts or exported YAML.
6. Enable per-action approval for writes, shell/code, notifications, database mutation, or ambiguous operations.
7. Test with a non-production target and idempotent request.
8. Inspect tool attempt/result and downstream state before broader use.

## Defaults and built-ins

Shipped default chat tools are `memory`, `read_webpage`, and `scheduler`. Defaults must be config-free. `notes` and `todo_list` cannot be default synthetic tools because their storage references persisted tool ids.

Agent-selectable built-ins include `scheduler`, `read_document`, `code_executor`, and `artifact_generator`; `read_document` is workflow-only in the picker. Code/artifact tools are not shipped as defaults because they require a sandbox runner. Headless scheduled/webhook runs exclude scheduler to prevent recursive scheduling.

## API/OpenAPI preflight

DocsGPT parses OpenAPI 3.x and Swagger 2.0 operations into actions for `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, and `OPTIONS`.

```bash
python scripts/validate_tool_spec.py openapi.yaml
```

The helper checks version, paths/operations, action names, base URL, risky methods, and unresolved external references without making requests. Review generated actions in the UI/API before saving.

## Side-effect rules

- Read operations can still expose sensitive data; approval is about both mutation and disclosure.
- For POST/PUT/PATCH/DELETE, require idempotency or a user confirmation boundary.
- Preserve SSRF protection; do not connect tools to loopback, link-local, cloud metadata, or private services unless an operator-approved network policy explicitly supports them.
- Limit database tools to least-privileged credentials and preferably read-only transactions.
- Sandbox and remote-device execution require separate isolation/approval; a tool description is not a security boundary.

## Cross-skill routes

- Attach tools to agents/workflows and headless runs: [agents-workflows](../agents-workflows/SKILL.md)
- Deploy sandbox/MCP/Redis/reverse proxy: [deploy-configure](../deploy-configure/SKILL.md)
- Use API clients or attachment streams: [api-client-operations](../api-client-operations/SKILL.md)
