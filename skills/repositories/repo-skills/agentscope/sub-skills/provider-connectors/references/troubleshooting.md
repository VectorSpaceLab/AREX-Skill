# Troubleshooting

## Missing extra or missing import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for a provider class | The provider extra was not installed | Install `agentscope[full]` or the narrow extra that owns the provider |
| A model class imports, but the embedding/TTS/provider helper fails later | The provider SDK is missing or out of sync | Re-check `pip check` and the installed distribution list with `../../../scripts/check_env.py` |
| `agentscope.model` imports but a specific family is unusable | That family needs a credential class or host that has not been configured | Use the credential constructor shown in `model-overview.md` and set the required env var or host |

## Credential and config mistakes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Wrong credential class passed to a model constructor | The provider family expects a different credential object | Switch to the credential class named in `model-overview.md` |
| Provider rejects the model name | The selected model is not one of the tested defaults | Compare against the model names in the overview reference or the unit tests |
| OpenAI-compatible provider responds with an unexpected base URL | The credential or client kwargs were aimed at a different endpoint | Check `base_url`, `api_host`, or provider-specific client kwargs |

## Embedding and TTS failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RAG or memory workflow fails after the embedding call succeeds | The embedding dimensions do not match the vector store | Re-read `embedding-overview.md` and the RAG sub-skill before changing the vector store |
| TTS output looks truncated or lifecycle events are missing | The wrong streaming/realtime style was chosen | Check the verified defaults in `tts-overview.md` and match the call style to the provider |
| Ollama provider tests fail locally | The local Ollama server is not running or the host is wrong | Start the server and re-check `OLLAMA_HOST` before changing the package install |

## Safe next checks

- `scripts/provider_matrix.py --list` to see which providers are importable and which env vars are set.
- `../../../scripts/check_env.py --show-backends` when the whole package looks stale.

## Escalation path

- If the issue is actually about retrieval or memory dimension matching, switch to `rag-memory`.
- If it is really about agent/tool wiring, switch to `agent-core`.
- If it is about service deployment or workspace backends, switch to those sub-skills instead.
