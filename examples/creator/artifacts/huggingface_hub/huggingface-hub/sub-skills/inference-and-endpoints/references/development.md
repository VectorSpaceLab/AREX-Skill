# Development Evidence And Generated-File Policy

This is a maintainer-facing reference for keeping the operating skill aligned
with the checkout. It is not a runtime route and does not authorize network,
model, or endpoint operations.

## Generated implementation evidence

- The published async client is generated from the sync client. The selected
  async implementation and native tests establish signature parity; do not
  hand-edit generated client files.
- The published inference types and their reference documentation are generated
  from task schemas. Use public exported types and method signatures at runtime;
  do not alter a generated type to paper over a provider response mismatch.
- The repository's inference-parameter checkers and type generator validate or
  regenerate those surfaces. They are maintainer tools, not commands for a
  Researcher.
- The package publishes an extra named `testing` (not `test` and not
  `inference`). It includes the pytest stack plus Pillow, NumPy, and soundfile;
  it does **not** include the `mcp` extra. Runtime users should install Pillow,
  NumPy, or `huggingface_hub[mcp]` only for the surface they actually use. The
  bundled mock script needs no testing extra because `httpx` is a base package
  dependency.
- The source `AGENTS.md`/Makefile policy uses `make style` and `make quality`
  for package development. Those commands can rewrite generated files and run
  broad checks; they are deliberately not part of this runtime skill.

## Evidence boundary

The router and references were distilled from the English inference, endpoint,
and MCP guides/package references; public source for the sync/async clients,
generated task types, provider helpers, MCP implementation, endpoint
APIs/classes and CLI; and selected inference-client, async-client, provider,
type, endpoint, and endpoint-helper tests. This checkout has no dedicated MCP
unit-test module, so MCP behavior is grounded in its English reference and
source rather than claimed as native-test coverage. Production/VCR tests are
evidence of individual service behavior but are not runtime dependencies. No
source checkout test fixture, cassette, credential, model download, endpoint,
or provider service is bundled.

When the package version changes, re-inspect constructor and representative
signatures, provider registry, endpoint status/payload behavior, MCP extra, and
the selected native tests. Update the references rather than claiming old
provider coverage is current. Keep any new checks deterministic with a mock
transport and redacted assertions.
