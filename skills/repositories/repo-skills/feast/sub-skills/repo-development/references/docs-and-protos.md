# Feast Docs, Protobufs, and Non-Python Components

## Documentation Placement

Use the documentation location that matches the change:

| Change type | Place content | Required follow-up |
|---|---|---|
| New online store | `docs/reference/online-stores/<name>.md` | Update store index/navigation docs |
| New offline store | `docs/reference/offline-stores/<name>.md` | Update store index, overview, and navigation docs |
| New registry backend | `docs/reference/registries/<name>.md` | Update navigation docs |
| Config option | `docs/reference/feature-store-yaml.md` | Include defaults and accepted values |
| CLI flag or command | `docs/reference/feast-cli-commands.md` | Match actual CLI behavior |
| How-to or integration guide | `docs/how-to-guides/` or a relevant customization subarea | Add navigation entry |
| Architecture or concept | `docs/getting-started/architecture/` or component concept docs | Consider ADR/RFC links for major changes |
| Blog post | `infra/website/docs/blog/` | Include YAML frontmatter: `title`, `description`, `date`, `authors` |

Blog rule: do not place blog posts under `docs/blog/` or any other directory. Blog posts belong under `infra/website/docs/blog/`.

For non-blog docs, ensure the page is discoverable from navigation. A correct content file without navigation is easy to miss in the rendered website.

## Docs Commands

Useful documentation targets:

```bash
make build-sphinx
make build-templates
make build-helm-docs
```

Meaning:

- `make build-sphinx` compiles Python protobufs first, then builds Python API source docs under the Python docs area.
- `make build-templates` runs the template compilation helper.
- `make build-helm-docs` regenerates Helm chart docs for Feast charts.

Run only the target relevant to the files changed. Do not run UI, Docker, or Helm commands unless the environment has the required tooling.

## Protobuf Workflows

Shared protobuf files live under the repository protobuf tree and affect Python, Go, generated docs, and serving APIs.

Common commands:

```bash
make compile-protos-python
make compile-protos-go
make compile-protos-docs
make protos
```

Use cases:

- `make compile-protos-python` runs the Python protobuf generation helper.
- `make compile-protos-go` installs Go proto tools as needed and regenerates Go protobuf bindings.
- `make compile-protos-docs` regenerates protobuf documentation output.
- `make protos` runs Python protobuf generation plus protobuf docs generation.

When `.proto` files change, check generated Python files and any language-specific generated outputs expected by the Makefile target. Add Go and Java checks if the proto affects serving APIs or generated client/server code.

Troubleshooting signal: protobuf deserialization errors, registry decode errors, stale generated classes, or missing fields after schema edits usually mean generated protobufs were not refreshed.

## Go Feature Server Awareness

The Go tree contains a Go feature server. Local build/run pattern:

```bash
go build -o feast-go ./go/main.go
./feast-go --type=http --port=8080 --metrics-port=9090
./feast-go --type=grpc --port=8081 --metrics-port=9091
```

Makefile checks:

```bash
make build-go
make test-go
make format-go
make lint-go
```

Notes:

- `make build-go` depends on Go protobuf compilation.
- `make test-go` compiles Python and Go protos, installs Go CI dependencies, installs Feast locally, and runs Go tests with coverage output.
- Go feature server metrics are exposed on a metrics port; `/health` is available on the main application port.
- OpenTelemetry tracing can be enabled with `ENABLE_OTEL_TRACING=true`; service name can be configured with `OTEL_SERVICE_NAME`.

Use Go checks for changes under `go/`, shared protobuf changes, or Python behavior that the Go feature server consumes.

## Java Serving Awareness

The Java tree contains serving components and a serving client. Makefile commands use Maven through the Java project file.

```bash
make format-java
make lint-java
make test-java
make test-java-integration
make test-java-with-coverage
make build-java
make build-java-no-tests
```

Use Java checks for changes under `java/`, shared protobuf/API changes that affect Java serving, or documentation updates that claim Java behavior.

Java integration tests are heavier than unit tests. Run `make test-java` first unless the change specifically requires integration validation.

## Operator and Docker Awareness

Feast includes Docker and operator-related targets. Treat these as environment-dependent:

```bash
make build-docker
make build-feature-server-docker
make build-feature-transformation-server-docker
make build-feature-server-java-docker
make build-go-feature-server-docker
```

Operator image targets run inside the operator area and require Docker tooling. Do not run push or publish targets unless the user explicitly asks for release engineering and credentials are configured.

## Difficult Case: Docs for a New Online Store

When adding docs for a new online store:

1. Create or update the online store reference page in the online store reference docs area.
2. Update the online store index/navigation so the page appears in rendered docs.
3. If configuration YAML is affected, update the feature store YAML reference.
4. If CLI flags or commands are added, update the CLI commands reference.
5. If the contribution also includes implementation, select tests using `testing-guide.md`.
6. Do not place the reference page in the blog directory. Use the blog directory only for a narrative blog post with required frontmatter.

Minimal verification plan:

```bash
uv run ruff check sdk/python/feast/infra/online_stores/<store>.py
uv run bash -c "cd sdk/python && mypy feast/infra/online_stores/<store>.py"
uv run python -m pytest sdk/python/tests/unit/infra/online_store/ -k "<store>" -v
make build-templates
```

If docs-only and no templates changed, a navigation/content review may be enough when docs tooling is unavailable.
