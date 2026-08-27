# LitServe installation and smoke checks

This reference is for the generated LitServe skill tree. It does not depend on
opening the source repository.

## Base install

```bash
pip install litserve
```

## Optional workflow packages

Install these only when you need the related sub-skill:

- `fastmcp` for MCP tool exposure.
- `Pillow` and `numpy` for image payload helpers and image round-trip examples.
- `openai` for SDK-style chat and embedding client examples.
- `httpx` and `asgi-lifespan` for ASGI client smoke checks.
- `requests` for simple HTTP examples and end-to-end demos.
- `python-multipart` for form and multipart file uploads.
- `psutil` for process-aware smoke checks and example helpers.

## Minimal smoke checks

```bash
python -I -c "import litserve as ls; print(ls.__version__)"
python -m pip check
litserve --help
litserve dockerize --help
```

For a slightly richer import smoke, run:

```bash
python scripts/smoke_import.py
```

For a runtime smoke that launches the bundled minimal server and exercises
`/health` plus `/predict`, run:

```bash
python scripts/smoke_server.py
```

## Deployment wrapper note

The package also exposes a `lightning` entry point that passes through to
Lightning SDK behavior. It may auto-install `lightning-sdk` if missing. Use that
wrapper only when you explicitly want the Lightning deployment CLI surface.
