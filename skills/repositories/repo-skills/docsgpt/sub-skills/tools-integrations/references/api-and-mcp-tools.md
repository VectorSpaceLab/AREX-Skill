# Generic API and MCP Tools

## Generic API tool

Use for bounded request/response REST actions. Prefer custom logic only when authentication, multi-step orchestration, streaming, signatures, or transformation exceeds the generic action model.

Each action defines:

- name, description, URL and method;
- query/path properties;
- headers;
- body properties and content type;
- static versus model-filled values;
- active state and approval policy.

OpenAPI 3.x or Swagger 2.0 can generate actions. The parser supports common parameter/body schemas and bounded local `$ref` resolution, but complex schemas can be simplified. Review every generated URL, required field, numeric mapping, body content type and action name.

### Security

- store API keys as static protected config, not model-filled arguments;
- use HTTPS and least-privileged credentials;
- block private/link-local/metadata targets and unsafe redirects;
- add timeouts and response-size limits;
- redact provider errors before sending them to the model;
- require approval/idempotency for mutation;
- do not use this tool for long-lived SSE/WebSocket connections.

## MCP tool

MCP lets DocsGPT discover and call tools from a remote server. Supported auth patterns include none, bearer, API key/header, basic, and OAuth.

Setup:

1. choose a server URL reachable from the backend;
2. select auth and configure credentials;
3. for OAuth, set a public `MCP_OAUTH_REDIRECT_URI` (or a correct public API URL fallback);
4. test connection without saving;
5. inspect discovered tools/resources;
6. save, complete auth and enable selected tools on an agent;
7. test one read-only action.

Useful backend endpoints include connection test/save, callback, and auth-status checks. OAuth completion also appears on the user event stream; Redis must be available for coordinated status.

### MCP cautions

- Discovery output is untrusted metadata; inspect tool schemas/descriptions.
- Remote server changes can alter capabilities without a DocsGPT release.
- Apply the same approval and side-effect policy as local tools.
- Cap timeouts (tool config supports bounded values) and output size.
- Distinguish backend reachability from browser reachability during OAuth.

## Validation ladder

1. bundled offline spec validator;
2. API/MCP test endpoint with non-production credentials;
3. save as disabled or on a draft agent;
4. one read-only action;
5. one approved write against a disposable target;
6. timeout, auth failure and malformed response cases;
7. verify logs contain no credentials.
