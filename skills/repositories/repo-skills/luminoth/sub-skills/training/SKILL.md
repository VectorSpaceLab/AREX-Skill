---
name: training
description: "Configures, runs, and evaluates Luminoth training jobs, including
  the optional Google Cloud ML workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Luminoth Training

Use this sub-skill when the task is to train or evaluate a Luminoth model, tune
a configuration file, or submit the same run to Google Cloud ML Engine.

## Route here for

- `lumi train` and `lumi eval` command planning.
- Merging one or more config files with `--config` and `--override`.
- Choosing between Faster R-CNN and SSD configs.
- Understanding `train.job_dir`, `train.run_name`, TensorBoard output, and
  evaluation watch behavior.
- The optional `lumi cloud gc` workflow, including `train`, `evaluate`, `jobs`,
  and `logs`.

## Do not use this sub-skill alone for

- Raw dataset conversion or TFRecord creation; route to
  [dataset-preparation](../dataset-preparation/SKILL.md) first.
- Packaging a trained run into a checkpoint or managing the checkpoint index;
  route to [checkpoints](../checkpoints/SKILL.md).
- Running predictions or the Flask demo after a checkpoint exists; route to
  [prediction](../prediction/SKILL.md).
- Cross-cutting install/import problems; start from the root
  [Luminoth](../../SKILL.md) router.

## Fast operating procedure

1. Read [references/configuration.md](references/configuration.md) for the key
   config fields and override syntax.
2. Read [references/workflows.md](references/workflows.md) for local train/eval
   commands and the cloud workflow summary.
3. Run the bundled preflight before you suggest a train or eval command:

   ```bash
   python scripts/check_config_keys.py --config ./config.yml --mode train
   ```

4. If the request involves Google Cloud, read
   [references/cloud.md](references/cloud.md) and confirm the required service
   account, APIs, and bucket setup.
5. If the task requires a run directory or checkpoint package, route that part
   to checkpoints instead of keeping it here.

## Common commands at a glance

```bash
lumi train -c ./config.yml
lumi train -c ./base.yml -c ./task.yml -o model.network.num_classes=3
lumi eval -c ./config.yml --split val --no-watch
lumi cloud gc train -c ./config.yml --bucket my-bucket --dataset gs://my-bucket/dataset
lumi cloud gc evaluate --train-folder gs://my-bucket/lumi_job --split val
```

## What this sub-skill owns

- Config file structure, defaults, and override syntax.
- Training and evaluation run directories.
- TensorBoard and other training outputs written under the job directory.
- Optional Google Cloud ML submission, listing, and log retrieval.
- Safe config preflight helpers that do not start training.

## What to delegate away

- If the request is about which images or annotations to ingest, move to dataset
  preparation.
- If the request is about a saved checkpoint alias or tarball, move to
  checkpoints.
- If the request is about inference, the demo server, or the public Python API,
  move to prediction.

## Working style

Keep the answer anchored to the config keys the code actually reads:

- `model.type`
- `dataset.type`
- `dataset.dir`
- `train.job_dir`
- `train.run_name`

Then explain any model-specific or cloud-specific fields only as far as the
current task needs them.
