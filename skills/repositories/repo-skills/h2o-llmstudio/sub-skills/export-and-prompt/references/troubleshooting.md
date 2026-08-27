# Troubleshooting

Use the preflight scripts first:

- `python scripts/check_experiment_artifacts.py ...`
- `python scripts/check_publish_inputs.py ...`

## Common failures

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Prompt setup fails before the model loads | The runtime location cannot resolve the prompt templates used by config loading | Confirm the prompt template directory exists in the same runtime context used to launch the prompt session |
| Prompt accepts a `--` command but nothing useful changes | The prompt parser expects `name value` pairs and uses the current field type for casting | Use exact prediction-field names and an even number of tokens, such as `--num_beams 4 --top_k 30` |
| Prompt output looks wrong for the trained data | The prompt format does not match the training format | Use the same prompt/answer/system tokens that the experiment used during training |
| Publish fails before upload starts | Missing `cfg.yaml`, missing `checkpoint.pth`, or an invalid device string | Run the experiment-artifact preflight and choose `cpu`, `cpu_shard`, or `cuda:<index>` |
| Publish fails on authentication | No write token and no usable Hugging Face login | Provide a write token or log in before running the exporter |
| Publish fails on network or Hub errors | Outbound access to Hugging Face is blocked, unstable, or the transfer helper is unhappy | Retry later, verify outbound access, and disable Hub transfer acceleration if needed |
| Publish fails when saving local export metadata | The output directory from the saved config is missing or not writable | Make sure the experiment output directory still exists and can be written to |
| Publish fails because the model name is rejected | The repo slug was not normalized to a Hub-safe name | Pick a cleaner model name before publishing |
| Export complains about disk space | Model preparation needs enough local free space before upload | Free space in the working directory before retrying |
| h2oGPT cannot load the exported model | The archive was not extracted or the base model points to the wrong target | Unpack the zip file and pass `--base_model` the repo id or extracted folder |

## Guidance by workflow

### Prompt sessions

- Prefer a CUDA device when available.
- Treat live parameter edits as temporary session changes.
- Re-run the prompt command after changing the saved experiment if you need a persistent update.

### Hugging Face publishing

- Leave safe serialization on unless a downstream consumer explicitly requires a different format.
- Use `cpu_shard` only when the runtime can actually see multiple GPUs.
- If the model repo name is derived from the folder name, review the normalized result before upload.
- If `user_id` is blank, the runtime resolves the logged-in account at publish time.

### Model cards and templates

- Missing model-card templates or summary templates are runtime setup problems, not Hub problems.
- If the wrong template family is selected, verify that the saved problem type matches the experiment you meant to export.
- Generation-style cards should include sample messages and generation settings; non-generation cards should not.

## Escalation checklist

If a failure is still unclear, collect:

- the exact command line,
- the experiment directory path,
- the selected device,
- whether a Hugging Face token was supplied or already cached,
- whether `HF_HUB_ENABLE_HF_TRANSFER` was enabled,
- the first error message from the preflight or runtime command.