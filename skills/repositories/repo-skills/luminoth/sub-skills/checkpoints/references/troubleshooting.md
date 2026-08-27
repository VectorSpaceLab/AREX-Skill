# Checkpoint Troubleshooting

## Purpose

Use this reference when checkpoint listing, downloading, importing, exporting,
or packaging fails.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `No checkpoints available.` | The local index is empty | Run `lumi checkpoint refresh` first or confirm `LUMI_HOME`. |
| `Checkpoint not found` | The id or alias is missing from the local index | Refresh the remote index or check the alias spelling. |
| `Checkpoint is not remote` | `download` was used on a local checkpoint | Use the id of a remote checkpoint, not a local one. |
| `Checkpoint is already downloaded.` | The remote checkpoint already exists locally | Use the existing local checkpoint or delete and redownload if needed. |
| `Checkpoint directory '...' already exists` | The target directory already has files | Remove the stale directory or choose a different checkpoint id. |
| `Couldn't find checkpoint in '...'` | `checkpoint create` could not find a TensorFlow checkpoint in the run directory | Verify `train.job_dir` and `train.run_name`, then wait for training to save a checkpoint. |
| `Tar file doesn't contain \`metadata.json\`` | The tarball is not a Luminoth checkpoint export | Re-export the checkpoint with `lumi checkpoint export`. |
| `Invalid file. Is it an exported checkpoint?` | The tarball is corrupted or not a valid tar archive | Use a valid exported checkpoint tar. |
| Duplicate alias warnings | Two checkpoints share the same alias | Prefer exact ids or clean up the duplicate entries. |

## Recovery workflow

1. Run `python scripts/inspect_checkpoint_index.py` to see the current index.
2. If the index is stale, run `lumi checkpoint refresh`.
3. If the checkpoint should already exist locally, inspect `LUMI_HOME` and the
   checkpoint directory directly.
4. If the problem is actually about a training run, route to the training
   sub-skill first.
5. If the problem is about using a checkpoint for inference, route to prediction
   after the checkpoint state is fixed.

## Notes

- Local and remote checkpoints share the same index file.
- Remote checkpoints can transition to local once they are downloaded.
- Export/import only preserves the metadata fields supported by the command.
