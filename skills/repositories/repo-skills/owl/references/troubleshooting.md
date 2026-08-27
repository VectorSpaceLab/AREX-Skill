# Cross-Cutting Troubleshooting

## Installation/import

If the package installs but `owl.utils` fails, run `pip check`, inspect the
installed CAMEL/MCP versions, and retry in a fresh private environment. The
inspected package's `camel-ai==0.2.84` import required an MCP 1.x runtime because
MCP 2.0 metadata resolved but did not export the `FastMCP` symbol CAMEL imports.
Do not repair a user-owned environment without approval.

## Credentials

A missing-key exception normally occurs during provider or image-toolkit
construction. Select a provider, validate variable names with the relevant
bundled helper, and keep values in a protected environment or secret manager.
Do not use a placeholder as proof of readiness.

## Optional services

Search, Firecrawl, Crawl4AI, Chunkr, Playwright, Docker, and GAIA data each add
network, system, credential, or cost requirements. If an optional service is
unavailable, route to a verified local/CPU path or report the capability as
unverified; do not silently claim equivalent coverage.

## Output and side effects

OWL can write generated files, logs, caches, extracted archives, result JSON,
Docker volumes, and `.env` values. Establish an explicit output/cache directory,
redact logs, validate downloaded/extracted input, and obtain authorization for
network or external-state changes before using code, file, browser, or Docker
tools.

For workflow-specific recovery, read the nearest sub-skill troubleshooting
reference: Workforce, document processing, web UI/deployment, or GAIA.
