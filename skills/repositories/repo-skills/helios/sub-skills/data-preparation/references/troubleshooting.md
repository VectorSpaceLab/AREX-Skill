# Data-preparation troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| JSON validation fails | A metadata item is missing `cut`, `crop`, `fps`, `num_frames`, `resolution`, `cap`, or `path` | Fix the record and rerun the bundled validator |
| Video path checks fail | The relative path is wrong or the clip was moved | Rebuild the dataset tree or update the metadata path |
| A bucketed file is skipped later in training | Frame count or resolution does not match the expected bucket | Re-run the preflight and keep only the intended resolutions |
| Prompt embeddings are missing | The prompt list has blank lines or the job was pointed at the wrong text file | Clean the text file and regenerate the embeddings |
| Latent filenames do not match the loader expectations | The file name does not encode `id_numframes_height_width` | Rename or regenerate the artifact before training |

## Practical reminders

- Validate the metadata before you start a distributed preprocessing job.
- Keep a tiny fixture around for layout checks.
- Do not confuse the validation layer with the heavy extraction jobs; the latter
  are environment-specific and often depend on local data roots.
