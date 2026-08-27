# Dependency Environment Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `@pypi decorator requires --environment=conda or --environment=pypi` | Flow used dependency decorator with local environment | Run with `--environment=pypi` or `--environment=conda`, or remove the decorator for local-only tests. |
| Step runs locally but remote task misses a file | Code package omitted a non-default suffix or dynamic file | Use `package list` and adjust `--package-suffixes`; avoid relying on files outside the code package. |
| Remote task cannot read S3/Azure/GS artifacts | Isolated step env lacks datastore-pinned libraries | Add required datastore libraries or use Metaflow's supported environment mode. |
| Resolver/bootstrap is slow or fails | Package pins conflict, network unavailable, or backend wheel unavailable | Narrow packages, pin versions, use supported Python, and avoid broad dev extras. |
| Decorator or environment plugin is missing | Plugin category disabled or extension not installed | Inspect plugin enablement and extension packages with the preflight script. |
