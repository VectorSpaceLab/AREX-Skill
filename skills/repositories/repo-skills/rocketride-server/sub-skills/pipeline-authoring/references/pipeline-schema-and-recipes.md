# Pipeline Schema and Recipes

This reference collects the JSON contract, wiring rules, and reusable shapes
for RocketRide `.pipe` workflows.

## 1) Pipeline contract

A `.pipe` file is JSON for one pipeline graph.

| Field | Role | Authoring rule |
| --- | --- | --- |
| `components` | Component graph | Required. Keep it as the first top-level field. |
| `project_id` | Pipeline identity | Required in hand-authored files. Use a literal UUID, not a placeholder. |
| `source` | Entry component id | Keep aligned with the real entry node when the file uses it. |
| `version` | Format version | Use `1`. |
| `viewport` | Canvas state | Preserve when editing an existing canvas; use defaults for new files. |
| `docRevision`, `isLocked`, `snapToGrid`, `snapGridSize` | Editor metadata | Preserve only when the task needs the existing canvas state. |
| `name`, `description` | Human-readable metadata | Optional. Keep if present in the file you are adapting. |

### Minimal skeleton

```json
{
  "components": [
    {
      "id": "source_1",
      "provider": "webhook",
      "config": { "hideForm": true, "mode": "Source", "parameters": {}, "type": "webhook" }
    }
  ],
  "project_id": "<uuid>",
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "version": 1,
  "source": "source_1"
}
```

## 2) Component contract

| Field | Role | Notes |
| --- | --- | --- |
| `id` | Unique component id | Must be unique within the pipeline. Keep ids stable when possible. |
| `provider` | Component type | This is the behavior selector. Use the node catalog for exact provider names. |
| `config` | Provider-specific settings | Holds profile selection, model settings, credentials, and node options. |
| `ui` | Editor layout | Optional canvas metadata only. |
| `input` | Data-lane edges | Lives on the receiving component. Each edge has `lane` and `from`. |
| `control` | Invoke edges | Lives on the controlled component. Each edge has `classType` and `from`. |
| `name`, `description` | Component labels | Optional documentation fields. |

### Connection roles

- **Data lanes** carry typed payloads such as text, documents, questions, or
  answers.
- **Invoke/control connections** attach an LLM, memory, or tool to the node
  that owns the runtime action.
- **Source nodes** do not receive data from upstream nodes.
- **Target nodes** are terminal components that return or persist results,
  such as response or store nodes.

## 3) Lane and connection rules

### Data lanes

Common lane names:

| Lane | Typical meaning |
| --- | --- |
| `tags` | Raw file metadata or source tags |
| `text` | Plain text |
| `table` | Structured rows |
| `documents` | Chunked or embedded document objects |
| `questions` | Query objects |
| `answers` | Model or search answers |
| `image` | Image payloads |
| `audio` | Audio payloads |
| `video` | Video payloads |

Rules:

1. The output lane of one component must match the input lane of the next.
2. Multiple upstream components may feed one downstream component.
3. One component may fan out to many downstream components.
4. Store/response nodes may be terminal endpoints when the workflow does not
   need a client response.

### Invoke/control connections

- Put `control` on the **controlled node**, not on the invoker.
- Use `classType` to match the invoke channel: commonly `llm`, `tool`, or
  `memory`.
- The `from` value is the component id that owns the invocation.
- An agent may invoke another agent as a tool; the sub-agent then owns its own
  LLM, memory, and tool controls.

### Source and target nodes

- Source nodes bring data into the pipeline. Common source archetypes are
  webhook, chat, and file dropper style entries.
- Target nodes return results or finalize a workflow. Common target archetypes
  are response nodes and store nodes.
- Source and target choices should match the user-facing entry and exit shape:
  conversational, document-driven, file-driven, or tool-driven.

## 4) Config patterns and env placeholders

### Source node config

```json
{ "hideForm": true, "mode": "Source", "parameters": {}, "type": "webhook" }
```

### LLM / embedding / vector DB patterns

```json
{
  "config": {
    "profile": "openai-4o",
    "openai-4o": { "apikey": "${ROCKETRIDE_OPENAI_KEY}" },
    "parameters": {}
  }
}
```

```json
{
  "config": {
    "profile": "miniLM",
    "parameters": {}
  }
}
```

```json
{
  "config": {
    "profile": "local",
    "local": { "host": "localhost", "port": 6333, "collection": "docs" },
    "parameters": {}
  }
}
```

### Agent / memory / response / prompt patterns

```json
{ "config": { "instructions": ["Use the provided context."], "max_waves": 10, "parameters": {} } }
```

```json
{ "config": { "type": "memory_internal" } }
```

```json
{ "config": { "laneName": "answers" } }
```

### Environment placeholder rules

- Use `${ROCKETRIDE_*}` strings for secrets and environment-specific values.
- Only string values are substituted.
- Do not use a placeholder for `project_id`.
- Do not hardcode provider keys, tokens, hosts, or collections if the pipeline
  is meant to be portable.

## 5) Reusable recipes

### A. RAG pipeline

```text
Ingestion: webhook -> parse -> preprocessor -> embedding -> vector store
Query:     chat -> embedding -> vector store -> prompt -> llm -> response
```

Key rules:

- Use the same embedding model for ingestion and search.
- Put the embedder before the vector store.
- Use `prompt` to merge retrieved documents with the question before the LLM.
- Keep collection names and provider credentials in environment variables.

### B. Document processing pipeline

```text
webhook -> parse -> ocr -> ner -> anonymize -> response_text
```

Key rules:

- Let `parse` split text, image, and other lanes from the source payload.
- Merge OCR text with the original text lane before downstream NLP if both are
  needed.
- Use `response_text` when the final output is text.

### C. Agent workflow

```text
chat -> agent -> response
          |
   +------+-------+
   |      |       |
  llm   memory   tool
```

Key rules:

- Attach the LLM, memory, and tool nodes via control connections.
- `agent_rocketride`-style workflows commonly use exactly one LLM and one
  memory node.
- Multi-agent comparisons can fan out from the same chat source and converge
  into one response node.

### D. n8n round trip

```text
RocketRide: webhook -> tool_n8n -> response_text
n8n:        Webhook -> ... -> Respond to Webhook
```

Key rules:

- The n8n workflow must be webhook-triggered to be called on demand.
- The n8n workflow should end in a response node for synchronous return.
- For round-trips, n8n can call back into a second RocketRide webhook pipeline
  and return that result to the original pipeline.

### E. Branch / join / tool sub-pipeline

```text
chat -> agent -> tool_pipe
                 ├─ branch_a -> join
                 └─ branch_b -> join -> response
```

Key rules:

- Keep the inline sub-pipeline self-contained.
- Do not feed the same sub-pipeline node from both the main flow and a control
  owner.
- Do not share a sub-pipeline node between two different control owners.
- End each branch in its own response node before the tool reads the result.

### F. Simple source-to-target sanity check

```text
source -> parse -> response
```

Use this when you want the smallest possible graph for a quick static check.

## 6) Static validation before an engine run

Validate the file in this order:

1. Parse as strict JSON.
2. Confirm `components` exists, is first, and is not empty.
3. Confirm every component id is unique.
4. Confirm every `input.from` points to a real component.
5. Confirm every `control.from` points to the correct invoker and the
   `classType` matches the controlled node.
6. Confirm all lane names line up with the producer/consumer pair.
7. Confirm source node config has the required fields for that source type.
8. Confirm terminal nodes match the final lane (`text`, `answers`, or storage).
9. Confirm `${ROCKETRIDE_*}` placeholders are used for portable secrets.
10. Confirm `project_id` is a literal UUID.
11. Preserve canvas metadata if the task is an edit rather than a fresh build.
12. Run the future static probe, when available, before any engine execution.

### Quick repair heuristic

- If only a value changes, edit `config`.
- If a node changes role, re-check `input` and `control`.
- If the source changes, re-check the whole graph.
- If a branch or sub-pipeline is involved, re-check ownership before runtime.
