# Training and playback troubleshooting

Use symptoms and the smallest bounded check first. Do not respond to a setup
failure by starting a full PPO run or an unbounded GUI loop.

| Symptom | Likely cause | Recovery / stop rule |
|---|---|---|
| TensorFlow or TFP import fails with a cloudpickle/gym conflict | Gym 0.17.1 and TFP 0.8 have incompatible dependency metadata, even when the legacy runtime can import | Preserve the verified legacy versions; inspect dependency metadata and import each package. Do not blindly upgrade Gym, TFP, or TensorFlow. Resolve the environment explicitly before launch. |
| `google.protobuf` descriptor errors, `Descriptors cannot be created directly`, or graph import crashes | Protobuf is too new for TensorFlow 1.15.5/TFP 0.8 | Use protobuf 3.20.3 in the isolated legacy environment, then run an import-only check. Stop if the host stack cannot provide it. |
| `--log-dir` is missing or a permission error occurs | Click requires it for `train`, or its parent is absent/not writable | Supply a writable path and check free storage. The trainer creates a timestamped child; do not use a private or ephemeral path as a shared recipe. |
| `Invalid value` for env, terrain, or mark | Click choice is case-sensitive or the value is not in the catalog | Use the choices shown by `rex-gym train --help` / `policy --help`: env `gallop|walk|turn|standup|go|poses`, terrain `mounts|maze|hills|random|plane`, mark `base|arm`. Route terrain meaning to the sibling environment skill. |
| `--arg` / `--flag` tuple parse error | A name/value pair is incomplete or has the wrong type | Supply `--arg NAME FLOAT` or `--flag NAME BOOLEAN`. Avoid repeated keys: later pairs overwrite earlier values. |
| Duplicate `--mark` shown or duplicate controller flags used | `policy` declares `--mark` twice in its Click help; both controller booleans are accepted | Pass `--mark` once. Pass exactly one of `--open-loop` and `--inverse-kinematics`; if both are passed, open loop wins. |
| Key error for a policy id such as `go_ik` | The environment/default mapping contains `go`, but the policy mapping has no Go entry | Treat it as unsupported packaged playback. Use only the eight catalog ids in [policy playback](policy-playback.md), or stop before launch. |
| Missing `config.yaml` | Package data was not installed, distribution is incomplete, or the selected id is unsupported | Run [the catalog inspector](../scripts/inspect_policy_catalog.py). Reinstall the public package in the compatible environment only if the package metadata confirms the asset should exist. Do not fabricate a config. |
| Missing `.data`, `.index`, or `.meta` checkpoint sidecar | Partial package or wrong checkpoint basename | Inspect the exact mapped basename; all three sidecars and `config.yaml` are required. Do not copy large binaries into the skill or recover a checkpoint from an unrelated policy. |
| Environment/controller task mismatch or `AttributeError` for a config function | The selected `<env>_<signal>` has no corresponding config or incompatible action/observation space | Check the default/controller table and the sibling simulation/modeling routes. `go` has a `go` config function but no `go_ik`/`go_ol` pair. Stop on a `BatchEnv` space mismatch. |
| Warning about agents not dividing updates, batch shape errors, or resource exhaustion | Agent count is inconsistent with update cadence or too large for the host | Use a positive, modest count; prefer a divisor of `update_every=25`. Playground intentionally uses one agent. The source warning is not complete validation. |
| `Session`, `tf.reset_default_graph`, `tf.contrib`, or restore API errors | A modern TensorFlow API is being used with this TensorFlow 1.x-style code, or protobuf/TFP is mismatched | Keep the legacy compatibility API and versions together. Run only import/config/asset checks until the v1 session and checkpoint restore are independently available. |
| No window, EGL/display error, or playback appears hung | PolicyPlayer creates a rendered environment and loops until `done`; GUI/display is unavailable or the task takes time | Do not treat the catalog check as GUI proof. Use a display-capable runtime and an external timeout only with explicit approval, otherwise report GUI playback unavailable. |
| Training consumes unexpected time/storage | Config step budgets are about 1e6–5e6, with summaries and checkpoints in the log tree | Stop before launch if the budget is not acceptable. Use help and catalog checks; never claim a bounded verification from a full run. |

When reporting a blocker, include the selected env/signal, whether it was train
or policy, the first failing bounded check, and whether the failure was a
missing dependency, package asset, writable path, display, or unsupported
combination. Do not include private installation paths or checkpoint contents.
