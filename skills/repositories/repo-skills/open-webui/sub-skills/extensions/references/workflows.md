# Extensions and Multimodal Workflows

## Typical setup sequence

1. Start Open WebUI from the deployment sub-skill.
2. Decide which extension surface you are using: function, tool, skill, pipeline, MCP server, browser helper, image backend, audio backend, or terminal helper.
3. Configure the relevant connection variables or manifest metadata.
4. Test the extension with a tiny example before promoting it to a real workflow.

## Extension surfaces

### Functions / tools / skills / pipelines

- These surfaces add behavior to the chat and agent flows.
- They often require a manifest, a tool server, or dependency declarations.
- If a manifest declares Python dependencies, install only what that extension actually needs.

### MCP / OpenAPI

- Use these when the user wants Open WebUI to speak to a tool server or API surface rather than a built-in function.
- Pay attention to the transport, auth, and timeout settings.
- A timeout failure is usually a transport or backend issue, not a chat-model issue.

### Browser helpers

- Browser-assisted helpers need the browser helper service and the correct loader engine.
- `WEB_LOADER_ENGINE=playwright` is the key signal for the browser-backed path.

### Image and audio extensions

- Image generation/editing and audio/voice features are extension-like workflows even though the user sees them in the UI.
- The backend connection or helper service matters more than the chat prompt.

### Terminal / code-interpreter style helpers

- These features usually combine a chat prompt, a tool server, and a service with side effects.
- Treat them like an integration problem, not like a model-selection problem.

## Practical checks

- Confirm that the extension service is reachable before trying a chat prompt.
- Test the smallest example payload first.
- Check timeout and SSL settings before changing the manifest.
- If the browser or image backend is missing, validate the helper service before retrying the UI.

## Configuration signals

- `ENABLE_PLUGINS`
- `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`
- `WEB_LOADER_ENGINE`
- `PLAYWRIGHT_WS_URL`
- `ENABLE_IMAGE_GENERATION`
- `AUTOMATIC1111_BASE_URL`
- `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER`
- `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL`
- `MCP_INITIALIZE_TIMEOUT`
