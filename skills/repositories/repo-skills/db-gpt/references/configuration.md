# Configuration and Version Boundaries

DB-GPT configuration is TOML-driven. Keep three concerns separate:

1. **Profile/provider model entries**: `[[models.llms]]`,
   `[[models.embeddings]]`, and optional `[[models.rerankers]]`; each needs a
   distinct role and provider-specific endpoint/key settings.
2. **Application/service settings**: web host/port, metadata database,
   workspace, storage, API behavior, and model-service topology.
3. **Workflow settings**: RAG chunk/retrieval parameters, AWEL/agent settings,
   datasource connector fields, or sandbox policy. Let the nearest sub-skill own
   these details.

## Safe configuration sequence

1. Copy a documented example into a user-controlled configuration location.
2. Replace provider keys with environment placeholders or secret-manager
   references; never paste a real key into a skill, fixture, or log.
3. Check that the chosen LLM, embedding, and optional reranker names are unique
   and that defaults refer to existing entries.
4. Validate TOML syntax and the expected table shape with the route-specific
   read-only checker before starting anything.
5. Resolve local relative paths against DB-GPT's configured home/workspace, not
   the original repository. Confirm directories and service ports explicitly.
6. Start one topology only, then verify the intended operation (chat,
   embedding, retrieval, flow, or file operation) rather than relying on a
   process or health response.

## Common environment signals

- `DBGPT_HOME` changes the application home/workspace boundary.
- `DBGPT_API_KEY` can protect client/API calls when the server is configured for
  API keys; the client sends it as a Bearer token.
- Provider-specific keys such as `OPENAI_API_KEY`, `MOONSHOT_API_KEY`,
  `DASHSCOPE_API_KEY`, `MINIMAX_API_KEY`, or `ZHIPUAI_API_KEY` belong only in
  the relevant runtime environment.
- `DBGPT_API_BASE` supplies the client base URL when a constructor does not
  receive one. Confirm whether the value should end at `/api/v2` for the
  Python client or use a raw endpoint prefix.
- `CONTROLLER_ADDRESS` may be used by model-management commands; an address
  that parses but cannot be reached is not a healthy controller.
- `CUDA_VISIBLE_DEVICES` selects visible GPUs, but does not install or verify
  a CUDA framework/backend.

## Version-sensitive checks

The recorded 0.8.1 CLI exposes `start web`/`start webserver` without a start
`--port` option; web port belongs in configuration. `stop webserver` accepts a
port selector. Model CLI option discovery can contact a controller. Always run
`dbgpt --help` and the relevant safe subcommand help against the installed
release when generating commands for a different version.

For provider fields, backend extras, RAG settings, and endpoint models, follow
these routes rather than copying a large configuration table into the root:

- [setup-and-cli configuration](../sub-skills/setup-and-cli/references/configuration.md)
- [models and provider matrix](../sub-skills/models-and-serving/references/provider-and-backend-matrix.md)
- [data/RAG workflows](../sub-skills/data-and-rag/references/workflows.md)
- [client/service endpoints](../sub-skills/apis-client-and-sandbox/references/service-endpoints.md)
