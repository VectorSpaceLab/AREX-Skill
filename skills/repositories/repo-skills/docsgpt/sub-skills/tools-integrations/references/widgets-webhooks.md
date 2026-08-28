# Widgets and Webhooks

## React widget

Install the published package:

```bash
npm install docsgpt
```

```jsx
import { DocsGPTWidget } from "docsgpt";

<DocsGPTWidget
  apiHost="https://api.example.com"
  apiKey="agent-api-key"
  title="Ask our docs"
  theme="dark"
  showSources={true}
/>
```

`apiHost` must be the DocsGPT API origin, not the frontend origin. Keep API keys scoped to an agent suitable for public exposure; browser code cannot keep a long-lived secret.

The legacy HTML bundle can render with `renderDocsGPTWidget`, but pin the package/CDN version and apply content-security-policy and supply-chain review.

## Browser integration checklist

- backend CORS allows the exact site origin;
- HTTPS/mixed-content rules pass;
- API host points to backend and reverse proxy supports streaming;
- exposed agent key has minimal sources/tools and can be rotated;
- source links do not leak private URLs;
- rate limits/abuse monitoring exist;
- widget error state handles auth, network and stream failure.

## Chatwoot bridge

The Chatwoot extension receives events, calls DocsGPT, and sends replies back with a Chatwoot access token. Configure separate DocsGPT API and Chatwoot URLs/tokens, scope the bot to the intended account/inbox/assignee, and honor the `human-requested` label to stop automated replies.

Run the bridge behind authentication/signature checks and a production WSGI server. Avoid generic `flask run` in production. Prevent message loops by filtering bot-authored events and make outbound sends idempotent.

## Agent webhooks

For asynchronous external triggers, use the agent webhook endpoint and poll task status. Webhook token is a secret; send `Idempotency-Key` for retries. See the agent automation reference for lifecycle and headless constraints.

Do not confuse:

- **widget/client chat**: interactive answer/stream request;
- **agent webhook**: asynchronous task trigger;
- **Chatwoot webhook**: third-party event bridge that may send a reply back.
