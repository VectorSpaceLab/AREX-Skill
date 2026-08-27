# Rex-Gym CLI reference

Read this when constructing a `train` or `policy` command. The CLI is a Click
group exposed as `rex-gym`; both commands use the same environment, argument,
controller, terrain, and mark parsing except where noted.

## Installation and help

The README targets Python 3.7:

```bash
python3.7 -m pip install rex_gym
rex-gym --help
rex-gym train --help
rex-gym policy --help
```

The package metadata exposes `rex-gym=rex_gym.cli.entry_point:cli`. The legacy
requirements include NumPy 1.17.3, pybullet 2.8.3, Gym 0.17.1,
TensorFlow 1.15.5, `ruamel.yaml`, Click, and TensorFlow Probability 0.8.
Treat the versions as a compatibility family, not as a recommendation to
upgrade individual packages.

## Options by command

| Option | `train` | `policy` | Meaning and source default |
|---|---:|---:|---|
| `--env`, `-e` | required | required | Click choice: `gallop`, `walk`, `turn`, `standup`, `go`, `poses` |
| `--arg`, `-a` | repeatable | repeatable | A `(str, float)` pair passed as an environment argument |
| `--flag`, `-f` | repeatable | repeatable | A `(str, bool)` pair passed as an environment flag |
| `--log-dir`, `-log`, `-l` | required | no | Parent for timestamped training output |
| `--playground`, `-p` | `False` | no | Boolean; playground means one agent and rendering |
| `--agents-number`, `-n` | `None` | no | Override the PPO environment batch count |
| `--open-loop`, `-ol` | false | false | Select `ol` |
| `--inverse-kinematics`, `-ik` | false | false | Select `ik` |
| `--terrain`, `-t` | `plane` | `plane` | Choice: `mounts`, `maze`, `hills`, `random`, `plane` |
| `--mark`, `-m` | `base` | `base` | Choice: `base`, `arm` |

Use the value-bearing tuple options as pairs, for example:

```bash
rex-gym train --env walk --log-dir ./logs \
  --arg target_position 1.0 --flag example_flag True
```

The accepted argument names and terrain behavior belong to the sibling
[simulation environments](../../simulation-environments/SKILL.md) route. The
robot model and controller semantics belong to
[locomotion modeling](../../locomotion-modeling/SKILL.md).

## Parsing details and hazards

The entry point merges `arg` and `flag` pairs into one dictionary. If the same
key occurs more than once, the later pair overwrites the earlier value. Avoid
repeated keys and verify the final command rather than assuming Click merges
values.

The parser returns `ol` when `--open-loop` is true, otherwise `ik` when
`--inverse-kinematics` is true, otherwise `None`; `None` invokes the environment
default mapping. Supplying both flags therefore silently selects `ol`. Treat
that combination as invalid in a preflight even though Click accepts it.

Click rejects an environment, terrain, or mark outside its choices. The
`policy` declaration currently exposes `--mark` twice in help, while `train`
exposes it once; do not repeat the option. A malformed tuple, a missing value,
or a lowercase/invalid boolean is a CLI input error, not a TensorFlow error.

## Controller/default table

| Environment | No controller flag | Resulting policy key when explicit |
|---|---|---|
| `gallop` | `ik` | `gallop_ik` or `gallop_ol` |
| `walk` | `ik` | `walk_ik` or `walk_ol` |
| `turn` | `ol` | `turn_ik` or `turn_ol` |
| `standup` | `ol` | `standup_ol` (no packaged IK entry) |
| `go` | `ik` | no supported packaged `go_ik` policy |
| `poses` | `ik` | `poses_ik` (no packaged OL entry) |

This table is the source mapping, not a statement that every environment/
controller combination is trainable or has a checkpoint. Check config and asset
presence with the bundled inspector first.
