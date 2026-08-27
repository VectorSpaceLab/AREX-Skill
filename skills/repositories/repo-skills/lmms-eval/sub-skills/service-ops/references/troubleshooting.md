# service-ops troubleshooting

Use this page when the HTTP server, MCP tooling, TUI/web UI, or job scheduler does not behave as expected.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The server does not start | Port conflict or missing `server` dependency | Try a different port and confirm the service extras are installed. |
| Jobs stay queued or never complete | The worker is blocked, the model process crashed, or the queue is backed up | Inspect the scheduler state and use the bundled service smoke before launching real work. |
| A job cannot be cancelled | The job is already running or has already finished | Check the current job status first; only queued jobs are cancellable. |
| MCP import or startup fails | The installed `mcp` package is incompatible with the expected FastMCP surface | Reinstall the MCP extra and rerun the service API smoke. |
| The web UI fails to build | The frontend toolchain or UI dependencies are missing | Verify the `tui` extra and the local Node.js toolchain before retrying. |
| Queue stats or job cleanup look odd | The scheduler state is stale or the cleanup retention is too low | Run the job-scheduler smoke and compare the behavior against the API reference. |

## Fast recovery steps

1. Confirm the service layer the user actually wants: HTTP server, MCP, TUI, or web UI.
2. Check `ServerArgs` and the client signatures before changing service code.
3. Reproduce with the bundled service smoke scripts.
4. Inspect queue and job state before attempting a restart.
5. If the problem is really about a model backend or task definition, route it to the owning sub-skill.
