# Troubleshooting

Use this reference when a `.pipe` file looks valid but does not run, does not
route data correctly, or fails static checks.

## Fast triage order

1. Parse the file as strict JSON.
2. Check component ids, `from` references, and lane names.
3. Check whether the problem is data flow or invoke/control flow.
4. Check source/target choice and terminal lane type.
5. Check environment placeholders and any missing credentials.
6. Check ownership rules if the workflow contains an inline sub-pipeline.
7. Run the static probe before trying the engine.

## Common failure patterns

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| File will not parse | Trailing comma, comment, bad quote, or malformed JSON | Open the file in a JSON-aware editor; verify `components` is valid JSON | Remove non-JSON syntax and keep the file strict JSON |
| `project_id` is rejected | Placeholder or reused id | Confirm it is a literal UUID | Generate a new UUID and keep it stable for that file |
| Pipeline opens but nothing flows | Lane mismatch or wrong `from` id | Compare the producer lane to the consumer lane | Rewire the edge or insert a converter node |
| Control nodes do not invoke tools or LLMs | `control` is on the invoker, or the `classType` is wrong | Check the controlled node, not the agent | Move the control edge onto the controlled node and use the correct class type |
| Memory seems ignored | Memory attached to a node type that does not support it | Confirm the agent type supports memory | Use a compatible agent or remove the unsupported memory edge |
| RAG search returns empty or low-quality matches | Embedder/store mismatch, wrong collection, or missing vector step | Compare ingestion and query embedder settings | Use the same embedding model and correct collection/host settings |
| Response node never returns | Final node does not match the lane produced upstream | Check whether the last lane is `text`, `answers`, or stored data | Swap to the matching response/target node |
| Env values stay literal in the file | Placeholder syntax is wrong or the key does not start with `ROCKETRIDE_` | Inspect each config string | Use `${ROCKETRIDE_NAME}` for strings only |
| Pipeline works in the editor but not at runtime | Source metadata or canvas metadata drifted from the real graph | Compare `source`, `version`, and source node ids | Normalize the metadata and rerun static checks |
| n8n call 404s or hangs | Workflow not active, wrong base URL, or response node missing | Confirm the target workflow is webhook-triggered and activated | Activate it, fix the URL, and end the workflow with a response node |
| Round-trip returns partial output | Shared sub-pipeline node or ownership conflict | Check whether a control-owned sub-pipeline is also used by the main flow | Make the sub-pipeline self-contained and give each control owner its own nodes |
| A branch result disappears | Join node flush order or branch wiring is wrong | Check the branch/join shape and whether each branch ends cleanly | End each branch in its own response node before joining or returning |

## Deep-dive checks

### Data flow versus control flow

If a node should receive payload data, it needs an `input` edge.
If a node should be invoked as an LLM/tool/memory dependency, it needs a
`control` edge on the controlled node.

### Source and target mistakes

- Do not invent a second source node to work around a missing lane.
- Do not use a response node with the wrong terminal lane type.
- Do not keep a source node disconnected from the rest of the graph.

### Sub-pipeline ownership mistakes

A control-owned inline sub-pipeline must remain isolated.

- One control owner per sub-pipeline node
- No data feed into a node that also owns a control-driven sub-pipeline
- No merging of sub-pipeline nodes back into the main graph

These mistakes usually surface as a partial result, a rejected pipeline open,
or a tool step that reads an incomplete sub-pipeline output.

### Validation before execution

If a workflow has already failed once, do not guess. Re-run the static checklist
from the schema reference, then only move to engine execution after the graph is
clean.

## Minimal repair playbook

1. Fix JSON syntax.
2. Fix ids and references.
3. Fix lane names.
4. Fix control ownership.
5. Fix env placeholders.
6. Run the static probe.
7. Only then try the engine again.
