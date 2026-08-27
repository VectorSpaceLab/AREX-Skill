# Argilla Python SDK troubleshooting

Start by separating SDK issues from server/deployment issues. This sub-skill covers Python SDK usage. If the failure involves starting the server, Docker/Kubernetes, Elasticsearch/OpenSearch, PostgreSQL, Redis, OAuth/SSO configuration, reindexing, or persistent storage, route to `server-ops`.

## Missing API key, API URL, or default client

Symptoms:

- `Missing api_key. You must provide a valid API key.`
- `Missing api_url. You must provide a valid API url.`
- Resource construction unexpectedly tries to create a default client.
- `Unauthorized` or credentials-specific errors during `rg.Argilla(...)`.

Fixes:

1. Instantiate the client explicitly before building resources:

   ```python
   client = rg.Argilla(api_url="<api_url>", api_key="<api_key>")
   dataset = rg.Dataset(name="my_dataset", settings=settings, workspace="argilla", client=client)
   ```

2. Or set `ARGILLA_API_URL` and `ARGILLA_API_KEY` before importing/constructing SDK resources.
3. Confirm that the API key belongs to a user with the required role. Dataset creation needs an owner or an admin assigned to the target workspace.
4. If the user is on a private Hugging Face Space, add the Hugging Face token as an HTTP header; do not replace the Argilla API key with the HF token.

## Server connection and API URL

Symptoms:

- Connection timeout, refused connection, or API route not found.
- Works in the browser but not from the SDK.
- Hugging Face Space URL from the embedded Hub page fails.

Fixes:

- Use the direct Argilla API/UI URL, usually `https://<owner>-<space>.hf.space` for Spaces or `http://localhost:6900` for a local server.
- In Spaces, if the browser is embedded, get the direct URL from the Space embed menu or from the Argilla UI "Import from SDK" snippet.
- Use `timeout=` and `retries=` for slow servers, but do not hide persistent connectivity failures.
- If a reverse proxy, base URL, CORS, or server process is the suspected cause, route to `server-ops`.

## Schema name collisions and settings validation

Symptoms:

- Settings validation says names are not unique.
- A property was silently replaced after calling `settings.add`.
- Dataset creation rolls back or fails while publishing settings.

Fixes:

- Ensure no field/question/metadata/vector share the same `name`.
- Use `settings.add(property, override=False)` during construction to catch accidental collisions.
- Keep at least one field and one question.
- `CustomField` requires a non-empty template string.
- For published datasets, prefer small updates such as titles, guidelines, metadata bounds, or custom templates. Major schema changes after records/responses exist may require a new dataset.

## Invalid record mappings

Symptoms:

- `Invalid attribute mapping format`.
- `Record has no identifiable keys`.
- Source columns are ignored with warnings.
- Responses log under the wrong question or as suggestions.

Fixes:

- Mapping targets must be `attribute[.type[.parameter]]`, where the attribute is a configured schema name or `id`.
- Use singular `.response` for ingestion mappings and pass `user_id=`. Flattened exports use plural `.responses` because they can contain multiple users.
- Questions default to suggestions. Use `.response` if the source is a human/existing label.
- Use `.suggestion.score` and `.suggestion.agent` for model metadata.
- Use the SDK's public external id target `id`; do not map to `external_id`.
- Check value formats against the question type. For example, multi-label values are lists, span values are lists of `{start, end, label}`, and ranking values are ordered lists.
- If you want one source value in multiple places, map it to a tuple/list of destinations.

## Image, chat, markdown, and custom field problems

Symptoms:

- Images do not render.
- Chat values fail validation or lose keys.
- Markdown media is too large or dimensions fail validation.
- Custom field renders blank.

Fixes:

- `ImageField` accepts URL strings, local paths available to the logging process, or PIL images. For long-lived UI rendering, prefer stable URLs or encoded/managed assets rather than temporary local paths.
- `ChatField` values must be a list of dicts with `role` and `content`. Extra keys are ignored; unknown message roles in `chat_to_html` raise errors.
- Markdown media helper width/height values must look like `300px` or `50%`. Keep embedded local files under the helper's 5 MB recommendation limit.
- For `CustomField`, ensure the field value is a dict and the template references the same keys, for example `{{record.fields.profile.name}}` with `fields={"profile": {"name": "Ada"}}`.
- Avoid `CustomField(template="https://...")` unless the user accepts a network dependency at runtime.

## Vector dimensions and similar search

Symptoms:

- Vector ingestion fails.
- `Similar` search errors or returns no scores.
- Search works for text but not vectors.

Fixes:

- Configure `rg.VectorField(name="embedding", dimensions=N)` before logging vectors.
- Every record vector under that name must have exactly `N` floats.
- Vector names should be URL-safe: letters, numbers, underscore, and hyphen.
- Use `dataset.records(..., with_vectors=True)` to fetch vectors.
- Similar search needs a server search backend and indexed vectors. If the error points to search service availability or reindexing, route to `server-ops`.

## Hugging Face Hub import/export and private Spaces

Symptoms:

- Hub push/download unauthorized.
- `Dataset.from_hub(..., settings="ui")` returns a URL string instead of a dataset.
- A private Space works in the browser but the SDK cannot connect.

Fixes:

- For dataset repos, pass the Hub token through Hub methods, for example `dataset.to_hub(repo_id, token=HF_TOKEN, ...)` or `rg.Dataset.from_hub(repo_id, token=HF_TOKEN, settings="auto", ...)`.
- For private Spaces, pass the Hub token through the SDK client's HTTP headers:

  ```python
  client = rg.Argilla(
      api_url="https://<owner>-<space>.hf.space",
      api_key="<argilla-api-key>",
      headers={"Authorization": f"Bearer {HF_TOKEN}"},
  )
  ```

- Keep the two credentials separate: the Argilla API key authenticates to Argilla; the HF token authorizes access to private Hub/Space infrastructure.
- Use `settings="auto"` or an explicit `rg.Settings` object if you need `Dataset.from_hub` to create a dataset programmatically. `settings="ui"` is a UI configuration flow.
- If `Settings.from_hub` cannot infer a question, add one explicitly or pass `feature_mapping={"column": "question"}`.

## Webhook URL, signature, event, and registration issues

Symptoms:

- Decorator execution creates a webhook unexpectedly.
- Webhook validation rejects `localhost` or a URL without a top-level domain.
- Events never reach the listener.
- Manual POST tests fail signature verification.

Fixes:

- The `webhook_listener` decorator registers/updates a webhook and creates a FastAPI endpoint when the decorator is executed. Keep decorators inside explicit setup code unless auto-registration is desired.
- Set `WEBHOOK_SERVER_URL` to the URL reachable from the Argilla server. For Docker-hosted Argilla calling a host listener, `http://host.docker.internal:8000` may be appropriate; for remote servers, use a public HTTPS URL.
- Avoid plain `localhost` for webhook URLs. Use an IP address or a host with a valid top-level domain as required by webhook validation.
- Use only supported event names: `dataset.created`, `dataset.updated`, `dataset.deleted`, `dataset.published`, `record.created`, `record.updated`, `record.deleted`, `record.completed`, `response.created`, `response.updated`, `response.deleted`.
- Incoming requests are verified with the webhook secret and standard webhook headers. A normal unsigned `curl` POST is expected to fail unless you intentionally use `raw_event=True` with properly signed payloads or bypass verification in a separate test app.
- Do not delete all existing webhooks as a cleanup step unless the user explicitly asks. Use the bundled webhook listener template for safe setup.

## Disk import/export problems

Symptoms:

- `to_disk` fails with file-exists errors.
- `from_disk` creates or reuses an unexpected dataset.
- Imported records do not match settings.

Fixes:

- Export to an empty directory. Argilla writes `.argilla/settings.json`, `.argilla/dataset.json`, and optionally `records.json`.
- `Dataset.from_disk` contacts the server, chooses a workspace, creates or reuses a dataset by name, and logs records when `with_records=True`.
- If the target name already exists in the workspace, provide a unique `name=` if the user's intent is to create a copy.
- If records fail to import, compare the exported record fields/suggestions/responses/metadata/vectors against the target settings schema and value formats.
