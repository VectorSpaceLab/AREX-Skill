# A2A Task Lifecycle

Bindu uses a task-first A2A JSON-RPC flow. The first `message/send` response confirms submission; the final answer normally arrives through `tasks/get` polling or streaming status events.

## Minimal `message/send`

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "00000000-0000-0000-0000-000000000004",
  "params": {
    "message": {
      "role": "user",
      "kind": "message",
      "parts": [{"kind": "text", "text": "hello"}],
      "messageId": "00000000-0000-0000-0000-000000000001",
      "contextId": "00000000-0000-0000-0000-000000000002",
      "taskId": "00000000-0000-0000-0000-000000000003"
    },
    "configuration": {"acceptedOutputModes": ["text/plain", "application/json"]}
  }
}
```

Expected immediate result: a task with `status.state` usually `submitted`. Do not expect the final artifact in the first response.

## Polling

```json
{
  "jsonrpc": "2.0",
  "method": "tasks/get",
  "id": "00000000-0000-0000-0000-000000000005",
  "params": {"taskId": "00000000-0000-0000-0000-000000000003"}
}
```

Use camelCase wire fields (`taskId`, `contextId`, `messageId`) unless targeting an older compatibility path that explicitly requires snake_case.

## States

| State | Meaning | Final? |
|---|---|---|
| `submitted` | Accepted and queued. | no |
| `working` | Worker executing. | no |
| `input-required` | Handler asks for more user input. | no |
| `auth-required` | Handler asks for auth/action. | no |
| `payment-required` | Payment layer blocks work. | no |
| `completed` | Final message/artifacts available. | yes |
| `failed` | Worker/handler failed. | yes |
| `canceled` | Task canceled. | yes |
| `rejected` | Task rejected. | yes |

## Worker flow

1. HTTP endpoint validates JSON-RPC and auth/payment middleware.
2. Message handler submits a task to storage and schedules it.
3. Worker loads task, validates state, and settles payment first when payment context exists.
4. Worker builds chat history from context/reference tasks.
5. `manifest.run(message_history)` executes the handler or gRPC callback.
6. Response detector maps structured states to open tasks or ordinary output to completion artifacts.

## Ownership and continuation

With auth enabled, storage records caller DID ownership for tasks and contexts. A caller cannot submit into another caller's context. To continue after a terminal task, use the same `contextId`, a new `taskId`, and optional `referenceTaskIds` pointing to prior tasks.
