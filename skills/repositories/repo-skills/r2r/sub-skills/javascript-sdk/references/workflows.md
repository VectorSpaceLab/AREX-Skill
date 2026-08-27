# JavaScript SDK Workflows

## Basic setup

```javascript
const { r2rClient } = require("r2r-js");

const client = new r2rClient("http://localhost:7272");
client.setApiKey(process.env.R2R_API_KEY);
```

## Login and token refresh

```javascript
const login = await client.users.login({
  email: "user@example.com",
  password: "password",
});
console.log(login.results.accessToken.token);
```

- The client can refresh tokens automatically when the callback options are set.
- Use `setTokens` when you already have access and refresh tokens.

## Document upload

```javascript
const result = await client.documents.create({
  file: { path: "./demo.txt", name: "demo.txt" },
  metadata: { title: "demo" },
  ingestionMode: "fast",
});
console.log(result.results);
```

- In Node, a string file path or `{ path, name }` object is supported.
- In the browser, pass a `File` object instead of a file path.

## Retrieval and streaming

```javascript
const response = await client.retrieval.rag({
  query: "What does the corpus say?",
  ragGenerationConfig: { stream: true },
  searchMode: "custom",
});

if (response instanceof ReadableStream) {
  const reader = response.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(new TextDecoder().decode(value));
  }
}
```

## Practical notes

- `searchMode` supports `basic`, `advanced`, and `custom`.
- `searchSettings` and `ragGenerationConfig` are JS objects that the client converts to the API shape.
- If you are building a browser app, make sure the server accepts your origin and that stream handling uses Web Streams APIs.
