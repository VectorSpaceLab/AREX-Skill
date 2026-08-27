# Flow Authoring Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Parameter name 'with' is a reserved word` or a Click option collision | A parameter name overlaps Metaflow CLI flags | Rename the parameter and use a different artifact attribute if needed. Avoid `with`, `tag`, `namespace`, `run-id`, `max-workers`, and similar flags. |
| `Metaflow could not determine your user name` | No username-like environment variable in automation | Set `USERNAME` or organization-supported `METAFLOW_USER` before local smoke runs. |
| Invalid `self.next()` transition | Missing `@step`, wrong target method, branch/join mismatch, or end step calls `next` | Run `python flow.py --no-pylint check`, inspect `show`, and ensure graph has one start and one end. |
| `IncludeFile ... direct reference ... cloud storage is no longer supported` | A cloud URI was passed to `IncludeFile` | Materialize the file locally first or pass a small pointer string through `Parameter`. |
| Join step loses or conflicts on artifacts | `merge_artifacts` conflict or branch-specific values | Explicitly collect values from `inputs` or exclude conflicting artifacts. |
| `pylint` missing | Optional lint dependency absent | Use `--no-pylint` for functional graph checks, or install lint tooling in a development environment. |
| Flow succeeds but `Run(...)` lookup fails later | Namespace/profile/metadata mismatch | Route to `client-and-data` and inspect namespace and metadata provider settings. |
