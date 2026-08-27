# MimicKit root troubleshooting

Use this page as the first stop for cross-cutting MimicKit failures. If the issue is specific to motion conversion, a particular training family, or SMP, switch to the matching sub-skill after this quick triage.

## Fast triage order

1. Is the checkout importable the same way the generated scripts expect?
2. Is the selected simulator backend installed?
3. Do the engine, env, and agent configs belong to the same recipe family?
4. Does every preset path exist from the target checkout root?
5. Are the required motion, model, or object assets actually present?

## Import and environment problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` for `mimickit`, `envs`, `learning`, or `engines` | The checkout is not on `PYTHONPATH`, and MimicKit is not packaged as an installable distribution in this snapshot | Run from the checkout root or use `sub-skills/runner-and-backends/scripts/run_mimickit.py`, which prepends the target checkout to `PYTHONPATH` |
| `pip install -r requirements.txt` succeeds but imports still fail | Dependencies are installed, but the source tree is not importable | Add the checkout root and `mimickit/` directory to `PYTHONPATH` |
| A bundled helper works in one directory but not another | The command relied on the current working directory | Pass an explicit `--repo-root` and use repo-relative paths that exist in the target checkout |

## Backend problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: isaacgym` | Isaac Gym is not installed | Install Isaac Gym or switch to a workflow that uses a backend you actually have |
| `ModuleNotFoundError: isaaclab` or `isaacsim` | Isaac Lab / Isaac Sim is not installed | Install Isaac Lab / Isaac Sim or use another backend |
| `ModuleNotFoundError: newton` or `warp` | Newton / Warp is not installed | Install Newton + Warp or switch backend families |
| Runner fails early even though the backend imports | The backend, asset format, or import order does not match the selected recipe | Re-check the engine YAML, the asset extension, and the bundled runner flow |

## Missing config or data problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Failed to load args from ...` | The `--arg_file` path is wrong or the preset file is malformed | Use a path valid from the target checkout root and keep comments on their own lines |
| `Unsupported engine`, `Unsupported env`, or `Unsupported agent` | The YAML names do not match a supported builder branch | Use one of the bundled config families from the checkout |
| `--mode` other than `train` or `test` | The runner only supports those two modes | Change the mode to `train` or `test` |
| Motion, checkpoint, or object file missing | The repo snapshot does not include all runtime assets | Download or restore the missing assets before trying a native run |
| `args/smp_dodgeball_humanoid_args.txt` points at a missing agent config | The checkout does not contain the matching dodgeball agent YAML | Treat that preset as a known gap and hand off to the SMP sub-skill |

## Safe-check failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The layout checker reports a missing core file | The wrong repo root was supplied, or the checkout is incomplete | Re-run the checker with the real MimicKit checkout root |
| The layout checker warns about missing external data | The repo intentionally does not ship all motions, models, logs, or object assets | Treat the warning as an asset-preparation task, not as a parser bug |

## Where to route next

- Motion conversion, motion viewing, DoF tests, or log plotting: `motion-tools`
- DeepMimic, AWR, LCP, or vault/static-object recipes: `motion-imitation`
- AMP, ADD, ASE, or task-conditioned adversarial control: `adversarial-control`
- TinyMDM prior training or SMP policy workflows: `smp`
- Shared runner, config triad, and backend readiness: `runner-and-backends`
