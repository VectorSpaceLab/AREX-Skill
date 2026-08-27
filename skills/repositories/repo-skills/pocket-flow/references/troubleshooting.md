# PocketFlow Cross-Cutting Troubleshooting

Read this when the failure spans setup, learners, custom models/data, and conversion.

| Symptom / question | Most likely owner | First action |
| --- | --- | --- |
| TensorFlow import or `tf.contrib` failure | Environment/setup | Read [execution-config troubleshooting](../sub-skills/execution-config/references/troubleshooting.md) and run its runtime probe. |
| Data path, `path.conf`, HDFS/local confusion | Execution/data | Validate config in [execution-config](../sub-skills/execution-config/SKILL.md), then check dataset contracts in [custom-models-data](../sub-skills/custom-models-data/SKILL.md). |
| Invalid learner id or compression flag confusion | Learner selection | Read [learner catalog](../sub-skills/compression-learners/references/learner-catalog.md). |
| Training starts but accuracy/performance is poor | Learner/data/model | Prove full-precision baseline, reduce compression severity, verify data labels/shapes, then tune learner flags. |
| Multi-GPU or idle GPU failures | Execution/backend | Probe `nvidia-smi`, Horovod, and TF-Plus with [check_runtime.py](../sub-skills/execution-config/scripts/check_runtime.py). |
| Custom model shape/label errors | Custom model/data | Read [custom-models-data troubleshooting](../sub-skills/custom-models-data/references/troubleshooting.md). |
| TFLite export or graph collection failures | Deployment/conversion | Read [deployment conversion troubleshooting](../sub-skills/deployment-conversion/references/troubleshooting.md) and validate artifacts first. |
| Seven/AutoML wrapper problems | Execution/AutoML | Treat Seven as environment-specific; use safe AutoML text helpers before cluster jobs. |

## Global recovery order

1. Verify Python/TensorFlow 1.x import and optional backend readiness.
2. Validate `path.conf` and dataset-key derivation.
3. Prove the selected run script with help/static checks.
4. Run or reason through a full-precision baseline before compression.
5. Add one learner/compression flag family at a time.
6. Export/deploy only after checkpoint artifacts are known good.

## Approval-gated operations

Ask before any operation that:

- Downloads datasets or pretrained model archives.
- Starts long training, evaluation, RL rollout search, Docker, Seven, `mpirun`, or mobile builds.
- Deletes/recreates logs, models, source checkout files, or non-temporary directories.
- Requires private HDFS, internal package mirrors, cluster credentials, or Android device access.

## Version caveats

PocketFlow is a 2018-era TensorFlow 1.x project. Modern Python, TensorFlow 2.x, modern TFLite APIs, and modern CUDA stacks may require compatibility work. Keep user-facing claims tied to the actual runtime being used.
