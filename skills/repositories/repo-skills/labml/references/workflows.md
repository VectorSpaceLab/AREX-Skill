# LabML Workflow Map

## Purpose

Read this when you need a quick map from a user request to the owning
subskill. The detailed APIs and failure modes live in the subskill references.

## Core workflows

| Workflow | Primary route | Typical signals | What to read next |
| --- | --- | --- | --- |
| Record an experiment | `sub-skills/tracking` | `experiment.record`, `tracker.save`, `logger.log`, `monit.loop`, `.labml.yaml` | `sub-skills/tracking/references/api-reference.md` and `sub-skills/tracking/scripts/tracking_smoke.py` |
| Configure runs and hyperparameters | `sub-skills/tracking` | `experiment.configs`, `lab.configure`, dynamic configs, git metadata | `sub-skills/tracking/references/workflows.md` |
| Monitor hardware and background services | `sub-skills/tracking` | `labml monitor`, `labml service`, `psutil`, `py3nvml` | `sub-skills/tracking/references/troubleshooting.md` |
| Build helper training loops | `sub-skills/helpers` | `DeviceConfigs`, `OptimizerConfigs`, `TrainValidConfigs`, `SimpleTrainValidConfigs` | `sub-skills/helpers/references/workflows.md` and `sub-skills/helpers/scripts/helpers_smoke.py` |
| Serve a dataset remotely | `sub-skills/helpers` | `DatasetServer`, `RemoteDataset`, FastAPI, uvicorn | `sub-skills/helpers/references/workflows.md` and `sub-skills/helpers/scripts/remote_dataset_smoke.py` |
| Set up remote projects and jobs | `sub-skills/remote` | `.remote/configs.yaml`, `prepare`, `job-run`, `helper-torch-launch` | `sub-skills/remote/references/cli-reference.md` and `sub-skills/remote/scripts/remote_config_smoke.py` |
| Start the monitoring app backend | `sub-skills/server` | `labml app-server`, MongoDB, settings files, analysis routes | `sub-skills/server/references/configuration.md` and `sub-skills/server/scripts/server_smoke.py` |

## Sample family map

- **PyTorch tracking samples**: use `tracking` for the core experiment, tracker,
  logger, and monitoring patterns.
- **PyTorch helper samples**: use `helpers` for `MNISTConfigs`, `CIFAR10Configs`,
  `SimpleTrainValidConfigs`, `DeviceConfigs`, and metric modules.
- **Lightning/Keras/FastAI examples**: use `tracking` for the LabML side of the
  integration and treat the framework-specific dependency as an optional extra.
- **Remote DDP examples**: use `remote` for job orchestration, not `tracking`.
- **Stocks and analytics examples**: use `tracking` for the LabML APIs and the
  app publishing workflow.

## Progression pattern

1. Choose the route that owns the user-facing trigger.
2. Read the relevant `sub-skills/<route>/references/api-reference.md` for signatures and options.
3. Read `sub-skills/<route>/references/workflows.md` for end-to-end usage.
4. Run `sub-skills/<route>/scripts/*_smoke.py` when you need a safe check.
5. If the workflow spans packages, follow the root `package-map.md` and the
   cross-cutting troubleshooting notes.
