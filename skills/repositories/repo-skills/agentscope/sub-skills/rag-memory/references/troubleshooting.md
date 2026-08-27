# Troubleshooting

## Dimension and collection mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Knowledge-base insert fails after the embedding step | The embedding dimension does not match the vector-store collection | Check `vector-stores.md` and rebuild the collection with the right dimension |
| Search succeeds but results look unrelated | The wrong embedding model or vector store was selected | Verify the model family, `dimensions`, and backend choice together |

## Memory-backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| mem0 local mode complains about Qdrant locks | Multiple local clients are using the same on-disk store | Share one client or switch to a remote Qdrant endpoint |
| mem0 ignores the backend kwargs you passed | `client` won over `mem0_config` | Re-check the constructor precedence; the tests deliberately cover this behavior |
| ReMe cards are written but not immediately searchable | The workspace needs a reindex | Run the reindex step from the demo pattern or wait for the background index loop |

## Workflow-level mistakes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `RAGMiddleware` does not inject anything | Wrong mode, empty knowledge base, or missing knowledge handles | Confirm the mode and the `KnowledgeBase` list first |
| `search_memory` / `add_memory` are missing from the agent | The memory middleware is not in the toolkit path you expected | Rebuild the agent with the middleware and toolkit shown in `workflows.md` |
| Filesystem memory cannot find the Markdown files later | The workspace directory changed between turns | Reuse the same workspace root and keep the `Memory/` folder intact |

## Provider-side issues that still look like RAG problems

- If the issue is the embedding model class itself, go to `provider-connectors`.
- If the issue is actually the workspace or file permissions, go to `workspace-sandboxes`.
- If the issue is how the agent loop handles tools or permissions, go to `agent-core`.
