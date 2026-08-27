# Backend Block Development

## Start with the SDK pattern

New provider-backed blocks normally use `backend.sdk` and a provider package under `backend/blocks/<provider>/`:

```python
from backend.sdk import BlockCostType, ProviderBuilder

my_provider = (
    ProviderBuilder("my_provider")
    .with_api_key("MY_PROVIDER_API_KEY", "My Provider API Key")
    .with_base_cost(1, BlockCostType.RUN)
    .with_description("Short provider description")
    .build()
)
```

Then create block classes that inherit from `Block`, define nested `Input` and `Output` schemas, and implement `async run()` yielding output pins.

## Block class checklist

- Use a stable UUIDv4 block id. Do not invent a placeholder or regenerate an id for an existing shipped block.
- Choose meaningful `BlockCategory` values so Builder search and filtering work.
- Define `Input` with `BlockSchemaInput`, `Output` with `BlockSchemaOutput`, and user-visible fields with `SchemaField` descriptions, defaults, and constraints.
- Use provider credential fields for API-key, OAuth, user/password, webhook, or managed-credential integrations.
- Prefer raising `BlockInputError` for user-fixable input validation and `BlockExecutionError` for expected runtime failures. Unhandled exceptions are treated as block failures.
- Include deterministic `test_input`, `test_output`, `test_mock`, and `test_credentials` when a block can be validated without network calls.
- Keep provider clients and API wrappers isolated in `_api.py`, models in `models.py`, and OAuth/webhook helpers in `_oauth.py` or `_webhook.py`.

## Credentials and providers

`ProviderBuilder` can declare API keys, managed API keys, OAuth, username/password, webhooks, base costs, descriptions, supported auth types, client factories, and error handlers. Provider descriptions and supported auth types are surfaced through integration-provider APIs for frontend settings and Builder connection UI.

For block-level credential schemas, use `CredentialsMetaInput[Literal[ProviderName.X], Literal["api_key" | "oauth2" | "user_password"]]` and `CredentialsField`, or use the provider object's `credentials_field()` when available. Never read API keys from arbitrary env vars inside `run()` if the credential system can own them.

## File and media blocks

Read workspace/media guidance before changing file behavior. In block code:

- Use `store_media_file(..., return_format="for_local_processing")` when a local tool needs a temp file.
- Use `return_format="for_external_api"` when sending bytes to an external model/provider.
- Use `return_format="for_block_output"` for returned media so CoPilot and graph contexts get the right representation.
- Require `execution_context` in `run()` for media work.
- Do not manually check workspace/session state to decide output format; let `store_media_file()` handle it.

## Testing blocks

Primary commands:

```bash
cd autogpt_platform/backend
poetry run pytest backend/blocks/test/test_block.py -xvs
poetry run pytest 'backend/blocks/test/test_block.py::test_available_blocks[BlockName]' -xvs
poetry run pytest 'backend/blocks/test/test_block.py::test_block_ids_valid[BlockName]' -xvs
```

The general block test harness uses each block's `test_input`, `test_output`, `test_mock`, and `test_credentials`. If a block needs credentials, external services, or nondeterministic outputs, mock the provider boundary and assert the semantic output pin rather than making a real call.

## Documentation and generated artifacts

Block docs are generated through backend tooling. Use the repository command instead of manually rewriting generated block tables:

```bash
cd autogpt_platform/backend
poetry run python scripts/generate_block_docs.py --help
```

Respect manual documentation sections and review generated diffs. If a schema or provider name change affects the frontend, export/regenerate OpenAPI and then use frontend API generation.

## Common block failure modes

- Missing `test_mock` causes native block tests to hit a provider or network.
- A credential field's provider/type does not match the provider registry.
- Output pin names do not match `Output` schema fields or downstream graph nodes.
- File blocks return local paths to graph outputs instead of `for_block_output` media references.
- `ProviderBuilder.with_oauth()` silently lacks OAuth support when required client id/secret env vars are absent; tests should not rely on secret-bearing defaults.
- Block costs or LLM model names drift from the catalog or `LLMModel` enum.
