# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Profile validation fails with missing fields | The Reddit JSON or Twitter CSV does not include every required schema field. | Add the missing fields and re-run [validate_oasis_profiles.py](../scripts/validate_oasis_profiles.py). |
| Custom prompt raises a missing-key error | `TextPrompt.key_words` does not match the keys in `UserInfo.profile`. | Make the template and profile keys match exactly, or flatten the profile into the keys your template expects. |
| Custom prompt warns about extra keys | `UserInfo.profile` contains keys that the template does not use. | Remove the unused keys, or keep them only if you intentionally ignore them. |
| `SocialAgent(..., model=None)` still fails | The CAMEL default model path is not configured or the required API key is missing. | Provide a model backend explicitly, or set the CAMEL/OpenAI credentials before creating the agent. |
| `available_actions` seems incomplete | Unsupported action names are being filtered out after a warning. | Use the canonical action names or `ActionType` values that the social action tools expose. |
| Neo4j graph creation fails | URI, username, password, or the live service is unavailable. | Fill in a valid `Neo4jConfig` and verify the database is reachable before using the Neo4j backend. |
| Visualization fails | `visualize(...)` only works with igraph, or the plotting stack is missing Cairo support. | Use the igraph backend and make sure the igraph/Cairo plotting dependencies are installed. |
| `close()` appears to do nothing | The graph is using igraph, not Neo4j. | This is expected; `close()` only shuts down the Neo4j driver. |

## Quick recovery order

1. Re-check the profile schema.
2. Re-run the bundled validator.
3. Fix custom prompt keys.
4. Confirm the model backend or API key.
5. Retry graph construction.
