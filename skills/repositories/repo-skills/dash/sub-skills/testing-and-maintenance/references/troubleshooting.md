# Testing and Maintenance Troubleshooting

## When to read

Read this when a Dash test, build command, formatter, or contribution workflow
fails.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dash_duo` or other pytest fixture is unavailable | `dash[testing]` is not installed | Install the testing extra in the active environment. |
| Browser integration hangs at startup | Server failed, browser/driver missing, or app import error hidden in logs | Run a single focused file with full output and inspect the traceback/browser logs. |
| `session not created` with ChromeDriver | Driver version does not match the browser | Install a matching driver before retrying browser tests. |
| Integration output does not show the real failure | Command was too broad or output was truncated | Re-run one file or one test-id pattern and preserve the full traceback. |
| Black/flake8/pylint command missing | Dev tools or formatter dependencies were not installed | Install the documented dev dependency and rerun. |
| Component build fails at `black` | Formatter not present in the active environment | Install Black before rerunning component generation/build commands. |
| `npm run build` or renderer tests fail | Node dependencies are missing or stale | Run `npm ci` first, then retry the specific package/renderer command. |
| Percy snapshot is absent | Percy token or browser-side setup missing | Treat Percy as optional unless the task explicitly requires visual regression. |

## Safe recovery sequence

1. Confirm the environment is the one you intend to use.
2. Verify the smallest focused test or CLI help command first.
3. If the task touches generated wrappers or bundles, confirm whether those
   artifacts need regeneration before rerunning the test.
4. Only then expand to browser or renderer tests.

## When to stop and ask

Stop and ask for more environment help when:

- A browser driver is missing and the task depends on browser tests.
- A Node build is required but Node/npm is not installed or is incompatible.
- A change needs a generated component refresh but the formatter/build tools are
  unavailable.
- The task needs a broader integration run but a focused test still does not
  reproduce the issue.
