# Memori Cloud Agent API

## Python entry points

| Method | Signature | Purpose |
| --- | --- | --- |
| `agent_recall` | `query=None, date_start=None, date_end=None, project_id=None, session_id=None, signal=None, source=None` | Fetch memories from the cloud agent recall endpoint |
| `agent_recall_summary` | `date_start=None, date_end=None, project_id=None, session_id=None` | Fetch summarized agent memories |
| `agent_compaction` | `project_id=None, session_id=None, num_messages=None` | Fetch a structured compaction |
| `capture_agent_turn` | `user_content, assistant_content, project_id, session_id=None, platform='python', trace=None, summary=None, provider=None, model=None, provider_sdk_version=None` | Persist an agent turn and send best-effort augmentation |
| `agent_feedback` | `content` | Send feedback to Memori Cloud |

## Parameter rules

- `session_id` is not valid without `project_id`.
- Cloud memory is keyed by the current attribution context. Set
  `entity_id`/`process_id` before expecting useful recall results.
- `capture_agent_turn` writes the durable turn first and only then attempts the
  best-effort collector augmentation request.

## Response shape notes

- Cloud recall and compaction methods return dictionaries from the remote API.
- The exact payloads are service-managed; this skill only documents the client
  contract and the safe failure boundaries.

## When to use

Choose this reference when the user asks about cloud memory API calls, result
filters, agent turn capture, or how to combine Memori with an application or
assistant runtime.
