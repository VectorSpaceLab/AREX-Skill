# Testing Rig Troubleshooting

## Common Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A group resolves to nothing | The group name, tier filter, or changed-file selection is wrong | Run `tests.rig list-groups` or `tests.rig expand` to see what the rig will actually run |
| An e2e group skips or fails before real assertions | The platform or infra service was not available | Check the selected runtime mode and the services it provisions |
| A group passes but coverage is missing | The group ran in the wrong tier or did not map to the path you expected | Check `coverage_source` and the critical-path registry |
| The run says a critical path is uncovered | The covering group did not run green in this lane, or the path has no active coverage | Check the manifest, the baseline, and the lane that can actually cover that path |
| Execute-path e2e tests fail immediately | `UNSTRACT_LLM_MOCK_RESPONSE` is missing | Set the mock response before starting the rig or the platform stack |

## Runtime Pitfalls

- `testcontainers` currently provisions only infra. If you need the full app stack, use `compose` or start the services locally yourself.
- `local` runtime respects existing `UNSTRACT_*_URL` values. Stale shell variables can make a local run point at the wrong stack.
- `optional` groups can legitimately skip when the infra they need is unavailable; that is not the same thing as a red failure.

## What To Check First

1. Confirm which tier can actually cover the path.
2. Confirm the runtime mode and the URLs it exports.
3. Confirm `groups.yaml` and `critical_paths.yaml` agree on the path mapping.
4. Confirm any execute-path tests have the required mock-response environment.
