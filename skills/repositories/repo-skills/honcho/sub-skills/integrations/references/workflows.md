# Integration workflows

## Workflow 1: Add Honcho to an app

1. Create or identify the application's workspace.
2. Create stable peers for the participants.
3. Create or reuse a session for the current conversation.
4. Add each turn as a message.
5. Read session context or peer representation before the next response.
6. Use peer chat only when you need a reasoned answer.

## Workflow 2: Ask a memory question

1. Identify the subject peer.
2. Decide whether you need current-session context or cross-session memory.
3. Pick the cheapest read surface that answers the question.
4. Narrow the search query or reasoning level when the question is broad.
5. Record the outcome so the next turn has better evidence.

## Workflow 3: Use the REST API directly

Use this when you are debugging the server or when the SDK does not expose a
specific route.

Typical request families:

- create workspace / peer / session,
- add messages,
- inspect context,
- query conclusions,
- inspect queue status,
- register or inspect webhooks.

## Workflow 4: Integrate TypeScript code

- Use the async SDK calls.
- Keep the workspace id stable.
- Preserve the same peer ids across turns.
- Store messages after each exchange.
- Prefer the SDK unless you need route-level debugging.

## Workflow 5: Compare SDK and REST behavior

When behavior looks inconsistent:

1. Check the SDK method signature.
2. Check the route family in the API map.
3. Compare the request scope and returned ids.
4. Inspect the same operation through the CLI if needed.

## Practical advice

- Keep peer ids stable.
- Keep one session per coherent thread or task.
- Choose the lightest read that answers the question.
- Do not expect immediate background memory updates after a write.
