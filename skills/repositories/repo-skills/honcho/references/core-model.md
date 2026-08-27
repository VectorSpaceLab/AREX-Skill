# Core model

Honcho is built around a small public model and a split runtime.

## Public concepts

| Concept | Meaning |
| --- | --- |
| Workspace | Top-level tenancy boundary. Most API routes are scoped to a workspace. |
| Peer | Any participant in the system, human or AI. Peers are the unit of representation. |
| Session | A conversation thread shared by one or more peers. |
| Message | Raw conversation data. Messages are what the system reasons over. |
| Conclusion | A derived observation stored about a peer. The API exposes these as conclusions. |
| Representation | The synthesized understanding of a peer, returned by reads such as `peer.chat()` and `session.context()`. |

## Runtime split

Honcho runs as two cooperating processes:

1. **API server** — FastAPI application that serves `/v3`, accepts writes, and enqueues background work.
2. **Deriver worker** — background consumer that updates memory and queue state.

A separate dreamer/consolidation path also runs off the queue when scheduled.

The key operational point is that message creation is not the same thing as
memory formation. A message can be accepted immediately while the derived
representation updates later.

## Read surfaces

Use the cheapest read that answers the question:

| Surface | What it gives you | When to use it |
| --- | --- | --- |
| `session.context()` | Session summary plus recent messages, and optionally a peer perspective | When you need the current conversation context |
| `peer.representation()` | A peer-focused summary across sessions | When you need a compact memory snapshot |
| `peer.chat()` | A reasoned natural-language answer | When a simple read is not enough |
| `peer.search()` / `session.search()` | Message search | When you need supporting evidence |
| `honcho doctor` | CLI health check | When you need to inspect deployment health quickly |

## Write surfaces

Common write operations are:

- Create or update workspaces, peers, sessions, and messages.
- Add peers to sessions.
- Store conclusions when the application wants to pin a durable fact.
- Configure API keys and server URLs through the CLI.

## Reasoning levels

The dialectic exposes the reasoning levels `minimal`, `low`, `medium`, `high`,
and `max`. Pick the lowest level that answers the question.

- `minimal` is the lightest factual lookup path.
- `low` is the default balance.
- Higher levels trade time and cost for deeper synthesis.

## Session and peer design

Good Honcho usage usually follows these rules:

- Keep one stable peer id per real person or agent.
- Keep a session scoped to one coherent conversation or task.
- Do not fragment a single interaction across many thin sessions.
- Use peer-targeted context when you want cross-conversation memory.
- Use session-scoped context when you only need the current thread.

## Data flow

1. Messages are written through the API or SDK.
2. The server stores the raw data and queues background work.
3. The deriver forms conclusions and updates peer representations.
4. The dreamer may later consolidate or refine memory.
5. Reads surface the latest available state without forcing synchronous reasoning.

## What to remember

The most common mistake is to expect immediate memory formation from a new
message. Honcho is designed around asynchronous reasoning, so the correct
pattern is: write the message, return to the user, and read the memory again
later when needed.
