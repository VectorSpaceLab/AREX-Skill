# Development And Testing Troubleshooting

Read this when source-checkout imports, focused tests, docs generation, migrations, or API changes fail.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `import mycodo` works but a module import fails | optional hardware dependency imported at top level | use static inspection or install only required optional dependency; avoid broad extras |
| Flask test app fails to create | missing base requirements, config/model/template import issue | run import smoke; inspect first traceback, not broad test output |
| Input tests fail on optional modules | hardware libs not mocked or dependency absent | use conftest mocks; run smaller `test_abstract_input_class.py` first |
| Custom module update tests fail | file upload fixture, unique-name comparison, or mocked subprocess behavior changed | inspect `utils_settings` and test fixtures; avoid real daemon restart |
| Docs generation rewrites many files | ran broad generation script or source metadata ordering changed | run family-specific generator; review generated diffs carefully |
| API endpoint tests return auth/media errors | missing API key fixture, wrong `Accept` media type, permission change | use v1 media type; update tests and docs together |
| Alembic migration conflict | head mismatch, model and migration diverged | inspect Alembic heads/history and post-upgrade hooks |
| Manual test blocks/hangs | accidentally ran hardware/network test on non-target host | stop test; mark as hardware-required; create focused synthetic/software check |

## Safe fallback strategy

1. Run import smoke with the bundled runner.
2. Run the smallest pytest target that covers the changed code.
3. If optional imports block tests, decide whether to mock, install the one dependency, or mark hardware-required.
4. Do not run full installer, Docker stack, backup/restore, or manual tests as a substitute for focused diagnosis.
5. Record skipped hardware/service checks explicitly; skipped is not passed.

## When to ask the user

Ask before installing system packages, changing a live Mycodo install, running Docker, running manual hardware tests, touching `/opt/Mycodo` or `/var`, using private credentials/API keys, or executing arbitrary user-supplied Python/Shell code.
