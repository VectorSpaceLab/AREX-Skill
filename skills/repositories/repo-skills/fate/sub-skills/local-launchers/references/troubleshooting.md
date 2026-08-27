# Local Launcher Troubleshooting

## Purpose

Use this when a service-free launcher import, context setup, data conversion, or training run fails. For FateFlow services, Pipeline upload/deploy/predict, or component CLI errors, route to sibling sub-skills instead of debugging them here.

## Quick triage

1. Run a cheap import check before spawning parties:
   ```bash
   python sub-skills/local-launchers/scripts/check_launcher_imports.py --check-standard
   ```
2. Confirm this is not a service-backed workflow. Local launchers should not require `fate_flow start`, `pipeline init`, uploaded tables, or a FateFlow endpoint.
3. Confirm the party list matches the algorithm family:
   - Hetero GLM/SecureBoost/Pearson/HeteroNN: `guest:9999 host:10000`.
   - Homo NN FedAVG: include `arbiter`, for example `guest:9999 host:10000 arbiter:10000`.
4. Confirm guest/host CSV paths and column names before training.
5. Treat any `launch(...)` execution as a heavy run: it starts one process per party and may perform cryptography or neural-network training.

## Missing `fate_utils`

Symptoms:

- `ModuleNotFoundError: No module named 'fate_utils'`
- import failures in crypto, Paillier, quantile, dataframe, or secure computation paths
- `pip check` reports an unsatisfied `fate_utils` dependency for `pyfate`

Likely cause: `pyfate` is installed without its companion `fate_utils` distribution or a compatible wheel/build.

Recovery:

1. Check metadata first:
   ```bash
   python - <<'PY'
   import importlib.metadata as md
   for name in ["pyfate", "fate_utils"]:
       try:
           print(name, md.version(name))
       except md.PackageNotFoundError:
           print(name, "NOT INSTALLED")
   PY
   ```
2. Install or repair the environment with the package versions selected by the root repo skill. Do not patch launcher code to bypass `fate_utils`.
3. Re-run the safe import helper before any training.

## Missing `pkg_resources` or `setuptools`

Symptoms:

- `ModuleNotFoundError: No module named 'pkg_resources'`
- package metadata or entry-point inspection fails even though `fate` imports partially

Likely cause: modern minimal Python environments may omit `setuptools`, which provides `pkg_resources`.

Recovery:

1. Check:
   ```bash
   python - <<'PY'
   try:
       import pkg_resources
       print("pkg_resources ok")
   except Exception as e:
       print(type(e).__name__, e)
   PY
   ```
2. Install `setuptools` into the active environment if package policy permits.
3. Re-run the helper. If the user supplied an existing environment, ask before making broad upgrades.

## Bad party tuples or rank errors

Symptoms:

- `ValueError: rank N is out of range M`
- a party appears as a malformed tuple after parsing
- guest/host/arbiter branch code does not run as expected

Likely causes:

- `--parties` omitted.
- Party values are not in `role:party_id` form.
- The number of parties does not match the algorithm.
- Homo NN was launched without an arbiter/server.
- Pearson was launched with more than one host even though the source implementation supports only one host.

Recovery:

- Hetero two-party command shape:
  ```bash
  python my_launcher.py --parties guest:9999 host:10000 --log_level INFO
  ```
- Homo FedAVG command shape:
  ```bash
  python my_homo_launcher.py --parties guest:9999 host:10000 arbiter:10000 --log_level INFO
  ```
- Do not use commas inside a single `--parties` value; pass parties as separate values after the option.
- In manual context code, use tuples and a matching list:
  ```python
  parties = [("guest", "9999"), ("host", "10000")]
  local_party = ("guest", "9999")
  ```

## Missing or mismatched CSV files

Symptoms:

- `FileNotFoundError` from `pandas.read_csv` or `CSVReader.to_frame`.
- Reader conversion succeeds on one party but training hangs/fails on the other.
- Guest has label errors or host unexpectedly tries to read a label.
- SecureBoost/SSHE/Pearson produces empty or mismatched joined samples.

Likely causes:

- The command uses recipe paths that do not exist in the user’s workspace.
- Guest and host use different match-id columns or non-overlapping ids.
- Guest lacks `label_name` while the selected recipe needs labels.
- Host includes a label column in a hetero recipe that expects host features only.

Recovery:

1. Confirm files exist before launching:
   ```bash
   test -f ./guest.csv && test -f ./host.csv
   ```
2. Inspect headers:
   ```bash
   python - <<'PY'
   import pandas as pd
   for path in ["./guest.csv", "./host.csv"]:
       df = pd.read_csv(path, nrows=3)
       print(path, list(df.columns), df.shape)
   PY
   ```
3. For breast-style hetero recipes: guest has `id`, `y`, feature columns; host has `id`, feature columns.
4. For motor-style SSHE LinR: guest label is `motor_speed`; match-id is `idx` on both sides.
5. For `PandasReader(sample_id_name=...)`, also set `match_id_name`; source validation rejects `sample_id_name` without `match_id_name`.

## Wrong local mode or context selection

Symptoms:

- Launcher unexpectedly asks for cluster addresses, Eggroll, OSX federation, or external services.
- Local examples fail with missing cluster config.
- Manual context creation works but `launch()` execution uses the wrong mode.

Likely causes:

- `--context_type cluster` was passed unintentionally.
- DeepSpeed/Eggroll tutorial code was mixed into a local launcher.
- A service-backed Pipeline example was adapted as if it were a local launcher.

Recovery:

- For normal local launchers, omit `--context_type` or set `--context_type local`.
- Use `create_context(..., federation_engine=STANDALONE, computing_engine=STANDALONE)` defaults unless the user explicitly asks for cluster/Eggroll.
- Route service-backed Pipeline code to `pipeline-workflows`; route FateFlow setup to `deployment`.

## GPU-only expectations

Symptoms:

- User expects CUDA or DeepSpeed acceleration during a local launcher run.
- PyTorch reports `torch.cuda.is_available() == False`.
- Hetero NN SSHE fails or is misconfigured when moved to GPU.

Grounded caveats:

- The verified construction baseline was CPU-only with `torch` 2.3.1+cpu.
- FATE Hetero-NN docs state multi-GPU training is not currently supported and the SSHE layer is incompatible with GPU training.
- DeepSpeed-on-Eggroll is a documented advanced path using Eggroll submission, non-local context engines, explicit ports, and GPUs; it is not verified as the default launcher route here.

Recovery:

- Keep CPU as the default path for SSHE LR/LinR, SecureBoost, Pearson, and Hetero/Homo NN examples unless the user supplies a verified GPU/DeepSpeed environment.
- For Homo NN local CPU testing, use `FedAVGClient(..., local_mode=True)` or `trainer.set_local_mode()` before federated launch.
- If the user needs DeepSpeed/Eggroll, make it a separate environment/deployment task and route installation/service prerequisites to `deployment`.

## SMPC `proc` import failures

Symptoms:

- `ModuleNotFoundError` for the module part of `module:Class`.
- `AttributeError` for the class part.
- `fate.ml.mpc` or `MPCModule` cannot be imported.
- The class exists but is not an `MPCModule` subclass.

Likely causes:

- The `--proc` string is misspelled or points at a class not installed in this environment.
- The installed distribution does not expose the SMPC module API used by the recipe.
- The class is a normal ML module, not an SMPC `MPCModule`-compatible class.

Recovery:

1. Use the safe checker:
   ```bash
   python sub-skills/local-launchers/scripts/check_launcher_imports.py \
     --proc some.module:SomeClass --expect-subclass-mpc
   ```
2. If the checker cannot import `MPCModule`, do not invent a substitute; mark SMPC `proc` execution unavailable for that environment.
3. If only the target class fails, correct the `module:Class` string or install the package that owns it.

## Multiprocessing and heavy-run failures

Symptoms:

- A cheap import check passes, but a launcher run exits after spawning ranks.
- Logs show one rank failed while others wait.
- The process appears slow or CPU-heavy.

Likely causes:

- Training is actually running; SSHE, SecureBoost, and NN recipes are not tiny by default.
- One party has bad data while another party is waiting for federation messages.
- A child rank raised an exception; inspect the rank-specific traceback printed by `MultiProcessLauncher`.

Recovery:

- Reproduce with the smallest CSV fixture that preserves labels/match ids.
- Lower epochs/trees/batch sizes in the launcher dataclass or constructor.
- Add preflight assertions before `inst.fit` or `trainer.train`: file exists, columns present, parties length matches algorithm, and `ctx.is_on_*` branches cover every role.
- Stop rather than silently retrying if the missing requirement is GPU, DeepSpeed, Eggroll, FateFlow service, or large external data.
