# Advanced Graphs and Pipelines Troubleshooting

Read this when a custom model, custom pipeline, migration, export, or visualization step fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A custom `DataPoint` does not deduplicate the way you expect | The model has no `identity_fields`, or the fields are not stable across runs. | Define identity fields deliberately and use `id_for(...)` only on values that should produce the same node id across runs. |
| The model import works, but extraction creates the wrong shape | The graph model and the prompt do not describe the same schema. | Revisit the custom graph model and make the prompt match the expected fields exactly. |
| `skip_connection_test=True` still fails | The custom tasks are actually calling LLM/embedding providers or the required config is incomplete. | Remove `skip_connection_test` only if the pipeline truly does not need provider connectivity; otherwise configure the backend first. |
| A migration source cannot be loaded | The archive/file path is wrong or the source format is unsupported. | Confirm the file/object type and the source mode before trying again. |
| Export returns an empty graph or no useful edges | The dataset has not been cognified, or the selected export format does not include the expected relations. | Rebuild the graph first, then export again with the correct format. |
| Visualization is too large or slow | The graph is huge and the render was not bounded. | Use `max_nodes`, a query, or seed node ids to shrink the visualization. |
| Temporal extraction seems ignored | `temporal_cognify=True` was not set, or the user asked for ordinary `search` tuning instead of extraction. | Re-run `cognify` with the temporal flag, then route query tuning to [search-retrieval](../../search-retrieval/SKILL.md). |

## Safe next checks

1. Inspect the model with the bundled helper:

   ```bash
   python scripts/inspect_custom_model.py --help
   ```

2. Verify the model import path and field annotations.
3. If the issue is provider, storage, or database related, route to
   [configuration-backends](../../configuration-backends/SKILL.md).
