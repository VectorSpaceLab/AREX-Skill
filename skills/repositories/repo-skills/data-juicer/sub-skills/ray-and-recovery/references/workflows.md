# Ray workflows

## Local Ray smoke
Use the bundled smoke helper first when you only need to confirm that Ray starts:

```bash
python scripts/ray_smoke.py
```

## Plain Ray execution
Use a recipe config with a Ray executor when you want distributed execution without partition recovery logic:

```bash
dj-process --config ray_recipe.yaml
```

## Partitioned execution
Use the partitioned executor when the dataset is large or you need checkpoint-based recovery.
Set the work directory, checkpoint directory, and event-log directory explicitly.

## Recovery flow
1. Run the job once.
2. Stop or interrupt it if needed.
3. Re-run with the same job identity and compatible settings.
4. Inspect the snapshot or monitor output before changing the config.

## Job helpers
Use the job snapshot, monitor, and stopper helpers to understand live state instead of guessing from the executor output.

## Good habit
If a Ray job fails, separate the problem into:
- Ray availability
- file visibility across workers
- partition / checkpoint configuration
- resume token or job ID mismatch
