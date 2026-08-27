# Framework troubleshooting

## `Parallel.runner` hangs or never reaches the callback

- Confirm the worker count, topology, protocol, and ports all match across the
  processes.
- Make sure the script has a real `if __name__ == '__main__':` guard when it is
  launched as a stand-alone file.
- Start with the bundled parallel smoke before trying a full example.

## Worker crash or auto-recovery failure

- If `auto_recover` is off, a worker crash is supposed to stop the whole run.
- If recovery is on, check the `max_retries` setting and whether the child is
  actually restartable.
- Use the bundled parallel smoke to isolate whether the problem is in the event
  path or the example script.

## `task.wait_for` times out

- The requested event name is probably never emitted, or the consuming middleware
  is not registered in the order you expect.
- Verify the runtime by running the bundled task smoke first.

## Pickling / spawn problems

- Lambdas or nested functions can break when the example needs multiprocessing.
- Move callback functions to top level if the script is going to be routed
  through `Parallel.runner` or a spawned child process.

## Message-queue backend problems

- `nng` is the normal backend for the framework runtime.
- `redis` requires its own extra services and is not part of the minimal CPU
  smoke path.
- If one backend fails, do not assume the other backend is automatically
  healthy; re-run the small smoke for the backend you actually need.
