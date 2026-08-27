# Plexe dashboard troubleshooting

This file covers dashboard-specific failures and saved-run inspection problems.
For install, backend, and provider issues, use the root
[`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## `No experiments found`

Cause:

- The workdir path is empty or wrong.
- No checkpointed Plexe run has been written to the directory yet.

Fix:

- Confirm the workdir path passed to `python -m plexe.viz --work-dir ...`.
- Use `scripts/inspect_workdir.py <work_dir>` to confirm whether any runs exist.

## Dashboard opens but the sidebar is empty

Cause:

- The saved experiments do not have the expected directory structure.
- The workdir contains files but not the `dataset/timestamp/checkpoints/` layout.

Fix:

- Check that the experiment root includes `checkpoints/*.json`.
- Confirm that the discovery layout matches Plexe's expected depth.

## `Error discovering experiments`

Cause:

- One of the experiment directories is unreadable or malformed.
- A checkpoint file contains invalid JSON.

Fix:

- Remove or repair the malformed experiment directory.
- Re-run the workdir inspector to identify the first bad path.

## `Error rendering dashboard`

Cause:

- A loaded checkpoint or YAML file is malformed.
- A derived report is missing a field the tab expects.

Fix:

- Inspect the latest checkpoint and the `.build/reports/` YAML files.
- Make sure the workflow completed the phase the tab is trying to render.

## Model package tab says `Model not yet packaged`

Cause:

- The experiment never reached Phase 6.
- The model package was deleted after training.

Fix:

- Check the latest checkpoint phase.
- Confirm whether `work_dir/model/` and `work_dir/model.tar.gz` exist.

## Search tree tab has no nodes

Cause:

- The search journal was not saved.
- The experiment never reached model search.

Fix:

- Check `checkpoints/04_search_models.json`.
- Confirm that the run completed Phase 4 before opening the tab.

## Evaluation tab is blank or partial

Cause:

- Final evaluation was disabled.
- `05_final_evaluation` is missing or did not complete.

Fix:

- Confirm whether a test dataset was provided.
- Inspect the evaluation checkpoint and the `05_final_evaluation` report.

## Practical inspection order

1. Check the workdir path.
2. Run `scripts/inspect_workdir.py`.
3. Confirm checkpoints exist for the target experiment.
4. Check whether `model/` and `model.tar.gz` were written.
5. Open the dashboard again once the filesystem looks correct.

