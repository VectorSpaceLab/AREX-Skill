# Auth and Webhooks

## When to Read

Read this when login, API-key validation, or webhook behavior is the source of a
problem.

## Authentication Paths

### JWT login

`POST /login` accepts an email/password payload and checks it against the `User`
row in the database. On success it creates a JWT access token using the
configured `JWT_SECRET_KEY` and expiry.

### GitHub OAuth

`GET /github-login` redirects to the GitHub authorize endpoint.
`GET /github-auth` exchanges the code, fetches the GitHub user, and either:

- reuses an existing `User` row and returns a redirect with an access token, or
- creates a new user and returns a first-login redirect.

The frontend redirect URL comes from `FRONTEND_URL`, defaulting to
`http://localhost:3000`.

### JWT-protected routes

Routes such as `/user`, `/validate-access-token`, and `/hello/{name}` require a
valid JWT access token and will reject missing or invalid credentials.

### API-key protected external routes

The `/v1/agent` family uses API-key based authentication through the helper
layer in `superagi.helper.auth` and associated controllers. When a request gets
`404` or `401`, verify both the API key and the target agent/project/org record.

### Provider-key validation

`POST /validate-llm-api-key` delegates to `build_model_with_api_key` for the
named provider and then calls its `verify_access_key()` method. This is a live
network/API validation path for real provider keys only.

## Webhooks

`/webhook` controller routes manage webhook records. The worker also emits status
changes through a webhook callback task in `superagi.worker`.

Practical points:

- Webhooks depend on database records and may reflect agent status transitions,
  not just explicit HTTP calls.
- If a webhook fails to fire, check the worker, database connectivity, and the
  event/status transition that should trigger the callback.

## Troubleshooting Hints

- A missing or placeholder JWT secret may allow startup but make auth behavior
  misleading.
- OAuth errors can arise from missing GitHub client credentials or an incorrect
  redirect URL.
- API-key routes require the org/agent context to match the key's organisation.
- Do not use the provider-key validation route as a no-cost smoke test; it may
  contact live services.
