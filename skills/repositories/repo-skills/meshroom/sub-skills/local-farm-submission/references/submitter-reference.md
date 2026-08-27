# LocalFarmSubmitter Reference

## Public Objects

Verified signatures include:

```text
LocalFarmSubmitter(parent=None)
LocalFarmJob(jid, submitter, farmPath=None)
FarmLauncher(root=None)
LocalFarmClient(root)
Job(name)
Task(name, command, metadata=None, env=None)
```

`LocalFarmSubmitter` is a `BaseSubmitter` with all submitter options enabled. It wraps Meshroom binaries, creates chunk tasks, retrieves `LocalFarmJob`, and provides job/task actions through the local farm client.

## Job Actions

`LocalFarmJob` supports:

- chunk actions: stop, skip, restart;
- job actions: pause, resume, interrupt, restart, restart error tasks;
- status/error inspection through `localfarmJob`, `localfarmTasks`, and `getJobErrors()`.

Use these methods only after identifying the job and farm root. They mutate task state and should be logged in a production incident.

## Environment and Rez

`getRequestPackages()` derives requested package versions from Rez environment variables. `rezWrapCommand()` optionally prefixes commands with a Rez environment. If Rez is not installed/configured, do not set Rez plugin mappings merely because a submitter supports them.

`wrapMeshroomBin(name)` uses a PATH command when available, otherwise falls back to the Meshroom `bin/` directory in the current installation.
