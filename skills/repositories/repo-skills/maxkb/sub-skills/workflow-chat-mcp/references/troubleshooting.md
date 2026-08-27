# Troubleshooting

## Common workflow/chat failures
- A node type is missing: confirm the backend registry and the workflow mode support list.
- A node behaves differently in stream vs block mode: check the `WorkflowManage` path that handles the current execution branch.
- A flow appears stuck: look for interruption-aware nodes or task-interrupt callbacks.
- A chat response is malformed: compare the response strategy (`system`, `openai`, or `loop`) and the SSE chunk wrapper.
- MCP returns `Method not found`: verify the JSON-RPC method name.
- MCP returns auth or publish errors: verify the application key and published state.

## Safe response pattern
- Name the execution surface first.
- Name the exact runtime mode next.
- Then describe the likely failing dependency or registry entry.

## Do not do
- Do not expose bearer tokens or API keys.
- Do not confuse frontend workflow-canvas issues with backend node execution.
