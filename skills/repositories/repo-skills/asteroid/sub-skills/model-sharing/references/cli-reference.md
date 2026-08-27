# CLI reference for model sharing

## `asteroid-upload`

```bash
asteroid-upload PUBLISH_DIR [options]
```

Important options:

- `--uploader`: required human name for the model author
- `--affiliation`: optional uploader affiliation
- `--git_username`: GitHub username used to build the upload name
- `--token`: Zenodo access token
- `--force_publish`: publish without the final interactive confirmation
- `--use_sandbox`: use Zenodo sandbox instead of the public instance

## `asteroid-register-sr`

```bash
asteroid-register-sr MODEL_FILE SAMPLE_RATE
```

Use this command only for older checkpoints whose serialized dict does not yet contain `sample_rate`.

## Safe local smoke scope

- `asteroid-upload --help`
- `asteroid-register-sr --help`
- local `save_publishable(...)` calls against a temporary directory
- `upload_publishable(..., unit_test=True)` if you are inspecting metadata without publishing
