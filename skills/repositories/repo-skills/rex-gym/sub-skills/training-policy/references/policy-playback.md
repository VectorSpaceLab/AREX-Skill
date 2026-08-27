# Packaged policy playback

Read this for a pretrained policy request. Playback is a rendered runtime
operation; the bundled inspector is the safe verification substitute.

## Catalog and mapping

`flag_mapper.ENV_ID_TO_POLICY` maps each supported policy id to a package-data
directory and a checkpoint basename. The package supplies `config.yaml` plus
TensorFlow checkpoint sidecars (`.data-00000-of-00001`, `.index`, `.meta`) for
these entries:

| Policy id | Package directory | Checkpoint basename |
|---|---|---|
| `gallop_ol` | `rex_gym/policies/gallop/ol` | `model.ckpt-4000000` |
| `gallop_ik` | `rex_gym/policies/gallop/ik` | `model.ckpt-2000000` |
| `walk_ik` | `rex_gym/policies/walk/ik` | `model.ckpt-2000000` |
| `walk_ol` | `rex_gym/policies/walk/ol` | `model.ckpt-4000000` |
| `standup_ol` | `rex_gym/policies/standup/ol` | `model.ckpt-2000000` |
| `turn_ik` | `rex_gym/policies/turn/ik` | `model.ckpt-2000000` |
| `turn_ol` | `rex_gym/policies/turn/ol` | `model.ckpt-2000000` |
| `poses_ik` | `rex_gym/policies/poses` | `model.ckpt-2000000` |

These are package assets, not files that should be copied into a generated
skill. Use:

From the generated skill directory, run:

```bash
python sub-skills/training-policy/scripts/inspect_policy_catalog.py --config-summary
```

The script reports package-relative paths, config presence, checkpoint-sidecar
presence, and small config summaries without loading YAML object tags or
reading checkpoint tensors. A missing sidecar means playback is not ready.

There is no `go_ik` or `go_ol` entry. Although `go` appears in the environment
and default-signal dictionaries, it is not a supported packaged policy.
Likewise, do not invent an IK standup or OL poses checkpoint.

## Playback command and sequence

A normal request has the following form:

```bash
rex-gym policy --env walk --inverse-kinematics --terrain plane --mark base
```

Omit the explicit controller only when the default table has been checked.
The command does not accept `--log-dir`, `--playground`, or `--agents-number`.
Environment arguments and flags use the same tuple syntax as training:

```bash
rex-gym policy --env poses --inverse-kinematics \
  --arg base_z 0.12 --flag on_rack True
```

The player sets debug mode, resolves `<env>_<signal>`, finds the package
installation's mapped policy directory, loads its `config.yaml`, creates the
environment with `render=True`, builds the simple PPO policy, and restores the
mapped checkpoint in a TensorFlow session. It repeatedly gets an action,
steps the environment, sleeps briefly, and exits only when `done` is true.
Thus a playback launch may require a graphical display and can run longer than
a bounded smoke check. It may also write TensorFlow/runtime logs.

## Safe acceptance boundary

A successful catalog check proves only that package metadata lists the small
config and checkpoint sidecars. It does not prove that the TensorFlow graph
restores, that the GUI works, that the policy is stable, or that the robot can
execute it. If GUI playback is unavailable, report that fact and stop; do not
replace it with a claim of policy quality or hardware readiness.
