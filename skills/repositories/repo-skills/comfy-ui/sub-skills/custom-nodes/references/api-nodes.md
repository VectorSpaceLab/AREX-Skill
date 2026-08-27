# API Nodes and Credentials

API nodes are provider-backed nodes that call online services through ComfyUI's API-node infrastructure. They are different from the server's public HTTP API: this reference covers node authoring and credential behavior only. For transport, queue, and server launch details, use `../../server-api/SKILL.md`.

## Public API-Node Pattern

Provider nodes use the public schema API and set `is_api_node=True`:

```python
from comfy_api.latest import IO

class ProviderImageNode(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ProviderImageNode",
            display_name="Provider Image",
            category="partner/image/provider",
            inputs=[IO.String.Input("prompt", multiline=True)],
            outputs=[IO.Image.Output()],
            hidden=[IO.Hidden.auth_token_comfy_org, IO.Hidden.api_key_comfy_org, IO.Hidden.unique_id],
            is_api_node=True,
        )

    @classmethod
    async def execute(cls, prompt):
        ...
```

When `is_api_node=True`, schema finalization also ensures credential-related hidden inputs are present, including Comfy Org auth/API-key and usage-source hidden values.

## Credential Rules

- Do not hardcode provider secrets in node source, workflow JSON, tests, or skill content.
- API-node credentials are hidden inputs supplied by the ComfyUI runtime/front-end account or configured API key flow.
- Document required provider accounts and billing separately from node code.
- Avoid printing tokens, request headers, or full upstream payloads in exceptions. Raise concise user-facing errors instead.
- Treat API-node output files, URLs, and provider responses as untrusted inputs; validate payload shape before converting to tensors or writing files.

## Disable Switch

ComfyUI has a `--disable-api-nodes` launch option. When enabled, API-provider nodes are not loaded and the frontend is prevented from API-node internet communication. If an API node is missing while local nodes load correctly, check this flag before debugging mappings.

## Provider Request Shape

Provider integrations typically combine:

- Pydantic request/response models for provider payload validation.
- `ApiEndpoint` declarations for proxy paths, methods, and query parameters.
- Helper calls for synchronous requests, polling requests, downloads, and uploads.
- Image/audio/video conversion helpers that validate and normalize upstream data into ComfyUI tensors.

Keep reusable provider clients inside the custom node package and make network timeouts explicit. Use async execution for network calls so ComfyUI's executor can schedule work correctly.

## Price and Billing Metadata

Public schema nodes can attach a `price_badge` that depends on widgets or inputs. If used:

- Ensure every referenced widget/input id exists in the schema.
- Keep pricing expressions informational and conservative.
- Do not rely on price badges as billing enforcement.

## Cross-links

- Use `public-node-api.md` for `IO.Schema`, `IO.Hidden`, and `IO.NodeOutput` mechanics.
- Use `../../server-api/SKILL.md` for launching ComfyUI, API-node server flags, CORS/TLS, and transport-level credentials.
- Use `../../workflow-execution/SKILL.md` for prompt validation and execution behavior when API nodes appear in submitted graphs.
