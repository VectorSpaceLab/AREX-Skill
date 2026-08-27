# Repository Development Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Pre-commit fails on a changed skill file | Formatting or linting mismatch. | Run `uv run pre-commit run --files <file>` on the changed file. |
| `check_import_rules.py` fails | A package imported across a forbidden boundary. | Fix the import direction or move shared logic into the allowed package. |
| `check_tool_registration.py` fails | Tool class was defined but not registered. | Add the module-level `register_tool(...)` call. |
| Persisted settings compatibility fails | Shape changed without migration or fixture. | Add a migration and update the historical fixture set. |
| `tests/examples/test_examples.py` fails | Example did not emit `EXAMPLE_COST:` or needs credentials. | Use the documented example-run environment and keep example outputs explicit. |
