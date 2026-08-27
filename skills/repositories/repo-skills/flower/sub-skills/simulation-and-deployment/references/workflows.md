# Workflows

## 1) Local development with a persistent managed SuperLink

Use this when you want to keep run history and logs on disk.

1. Check the active profile with `flwr config list`.
2. Make sure the profile you want is the default or pass it explicitly.
3. Use a local app directory and run:

   ```bash
   flwr run .
   ```

4. Inspect the run with:

   ```bash
   flwr list
   flwr log <run-id> --stream
   flwr stop <run-id>
   ```

5. Remember that `flwr stop` only stops the run. It does not stop the background
   managed local SuperLink.
6. If the local SuperLink needs to be restarted, stop the stale `flower-superlink`
   process separately and then rerun `flwr run .`.

Typical profile shape:

```toml
[superlink]
default = "local"

[superlink.local]
address = ":local:"
```

## 2) Local development with in-memory SuperLink state

Use this when the on-disk local SuperLink state causes SQLite locking or when the
machine uses a slow or shared filesystem.

1. Stop the existing background local SuperLink first.
2. Switch the profile to in-memory state:

   ```toml
   [superlink.local]
   address = ":local-in-memory:"
   ```

3. Run the app again with `flwr run .`.
4. Re-create or inspect the run as usual with `flwr list`, `flwr log`, and `flwr
   stop`.

Tradeoff: in-memory mode does not persist old run history or logs after the managed
local SuperLink stops.

## 3) Simulation Runtime tuning

Use this when you want to change the number of virtual SuperNodes or the resources
assigned to each ClientApp worker.

1. Set default Simulation Runtime values for the selected SuperLink profile:

   ```bash
   flwr federation simulation-config \
     --num-supernodes 100 \
     --client-resources-num-cpus 4 \
     --client-resources-num-gpus 0.25
   ```

2. Run the app as usual. The managed local SuperLink uses those defaults until you
   change them.
3. For a single run, override the defaults with `--federation-config`:

   ```bash
   flwr run . --federation-config="num-supernodes=256 client-resources-num-cpus=1"
   ```

4. Use `--init-args-num-cpus` and `--init-args-num-gpus` when you want to cap how much
   of the host machine the Simulation Runtime may see.
5. Treat `client-resources` as soft concurrency controls. They are not strict memory
   limits.

When you need multi-node simulation:

- Use the same Python environment on every node.
- Use the same code and the same dataset or dataset partitioning inputs on every node.
- Start Ray on the head node with `ray start --head`.
- Attach the other nodes to the Ray head.
- Launch `flwr run` from the head node.
- Run `ray stop` on each node when finished.

On Windows, prefer WSL2 unless you already know the Ray setup is supported well in the
current environment.

## 4) Deployment runtime with SuperLink and SuperNodes

Use this when you want to run a Flower App against a long-lived SuperLink and one or
more long-lived SuperNodes.

1. Start the SuperLink in a terminal:

   ```bash
   flower-superlink --insecure
   ```

   Use TLS flags instead of `--insecure` for a real deployment.

2. Start one or more SuperNodes in separate terminals:

   ```bash
   flower-supernode \
     --insecure \
     --superlink 127.0.0.1:9092 \
     --clientappio-api-address 127.0.0.1:9094 \
     --node-config "partition-id=0 num-partitions=2"
   ```

3. Add a named connection profile to the Flower Configuration file and point it at the
   SuperLink address:

   ```toml
   [superlink.local-deployment]
   address = "127.0.0.1:9093"
   insecure = true
   ```

4. Run the app against that profile:

   ```bash
   flwr run . local-deployment --stream
   ```

5. Use `flwr config list` to confirm which profile is default before you start another
   run.

Remote app specs are also supported. When the app already lives on Flower, use the
remote spec form instead of a local path:

```bash
flwr run @account_name/app_name remote-profile
```

## 5) Authentication and TLS

Use this when the SuperLink connection is remote or otherwise protected.

1. Define a non-insecure profile with an address and a root certificate path:

   ```toml
   [superlink.remote]
   address = "superlink.example.com:9093"
   root-certificates = "/absolute/path/root-ca.crt"
   ```

2. Authenticate with:

   ```bash
   flwr login remote
   ```

3. Reuse the same profile with `flwr run`, `flwr log`, `flwr stop`, `flwr pull`, and
   `flwr list`.
4. Keep `insecure = true` only for local testing.
5. If a command returns an authentication error, re-check the selected profile,
   certificate path, and login state before trying again.

## 6) FAB packaging and install

Use this when you want to move a Flower App as a bundle.

1. From the app directory, build the FAB:

   ```bash
   flwr build
   ```

2. Install it on another machine or into a clean Flower home:

   ```bash
   flwr install ./publisher.app.version.hash.fab
   ```

3. Use the installed bundle as the starting point for a later run or handoff.

## 7) Practical selection rules

- Use `:local:` when you want persistence.
- Use `:local-in-memory:` when filesystem locking or shared storage causes problems.
- Use a named connection profile when you want to point the CLI at a specific
  deployment.
- Use `flower-superlink` and `flower-supernode` when the deployment itself needs to be
  started or debugged.
- Use `flwr federation simulation-config` for durable simulation defaults.
- Use `--federation-config` when you want a one-off simulation override.
