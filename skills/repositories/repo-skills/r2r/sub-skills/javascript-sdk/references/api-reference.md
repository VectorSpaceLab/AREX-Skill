# JavaScript SDK API Reference

## Client constructor

- `new r2rClient(baseURL, anonymousTelemetry = true, options = {})`

## Options

- `enableAutoRefresh`
- `getTokensCallback`
- `setTokensCallback`
- `onRefreshFailedCallback`

## Client helpers

- `client.setTokens(accessToken, refreshToken)`
- `client.setApiKey(apiKey)`
- `client.setProjectName(projectName)`
- `client.unsetProjectName()`
- `client.getRefreshToken()`

## Nested client groups

- `client.chunks`
- `client.collections`
- `client.conversations`
- `client.documents`
- `client.graphs`
- `client.indices`
- `client.prompts`
- `client.retrieval`
- `client.system`
- `client.users`

## Important JS conventions

- Request keys use camelCase in JS and are converted to the snake_case API shape as needed.
- The request helpers mirror the Python/REST workflow names, but the payload keys use JS-style names such as `searchMode`, `searchSettings`, `ragGenerationConfig`, `collectionIds`, and `ingestionMode`.
- File uploads use `file` with a Node path, `File`, or `{ path, name }` object depending on runtime.
