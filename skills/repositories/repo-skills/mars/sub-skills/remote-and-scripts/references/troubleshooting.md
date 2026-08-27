# Remote Troubleshooting

## Common failures

### Spawn returns an object but nothing seems to run

**Symptoms**
- The returned object prints successfully, but no final value appears.

**Likely cause**
- `spawn` is lazy. Execution starts only when `.execute()` is called.

**Recovery**
- Call `.execute().fetch()` on the spawned object.

### One remote result should feed another, but the dependency breaks

**Symptoms**
- A later spawned function receives the Mars object rather than the concrete
  value you expected.

**Likely cause**
- The caller did not pass the spawned object directly or misused kwargs.

**Recovery**
- Pass the remote object itself as an argument to the next `spawn` call.
- Keep the argument shape simple and use `ExecutableTuple` for explicit fan-in.

### `fetch_log()` returns nothing

**Symptoms**
- Log retrieval is empty even though the function printed output.

**Likely causes**
- The session is not distributed.
- The task has not finished yet.
- The offsets were already consumed.

**Recovery**
- Confirm that the runtime is a distributed session before relying on logs.
- Try `fetch_log(offsets=0)` when you need to reread from the start.

### `run_script` is not the same as `spawn`

**Symptoms**
- A user expects a script to run like a function and gets a mismatched
  environment or argument contract.

**Likely cause**
- `run_script` is a script-style workflow with its own worker-side contract.

**Recovery**
- Read the API reference and distinguish callable fan-out from script-style
  execution.
- Use the bundled smoke helper for the safe local path and defer full script
  execution to a proper runtime.

### `WORLD_SIZE` or worker environment variables do not match

**Symptoms**
- A script assumes a specific worker count or env contract and fails.

**Likely cause**
- The runtime did not launch the number of workers the script expected.

**Recovery**
- Check the user-supplied `n_workers`, and assert the script sees
  `WORLD_SIZE`, `RANK`, and the injected `session` object.
- Do not rely on the original repo's sample script as runtime guidance; wrap
  the contract in your own bundled helper instead.
