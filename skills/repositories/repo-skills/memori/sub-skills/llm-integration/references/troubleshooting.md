# LLM Integration Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Unsupported provider error | the client object or provider name is not recognized | use a supported direct client or named framework argument |
| Mixed direct/framework error | `client=` was combined with framework arguments | choose one registration mode per call |
| Agno and LangChain mixed together | two framework families were passed at once | split the registrations into separate calls |
| LangChain passed as `client=` | the model object came from LangChain but was given the direct-client route | use the matching named argument such as `chatopenai=` |
| Missing SDK object shape | the provider package was not installed or the object does not match the expected client class | install the correct provider SDK and instantiate the documented object |
| No recall appears after registration | attribution was skipped, the script exited too early, or `augmentation.wait()` was omitted | set attribution and wait for the write path to settle |
| Deprecated accessor warning | older `memori.<provider>.register(...)` path was used | migrate to `mem.llm.register(...)` |

## Recovery order

1. Identify whether the user has a direct client or a framework model.
2. Use the matching route once and avoid mixing provider families.
3. If the provider is OpenAI-compatible, keep the direct OpenAI path and only
   adjust the base URL or transport details.
4. If the registration is correct but the memory still looks empty, hand the
   user back to `memory-and-search`.
