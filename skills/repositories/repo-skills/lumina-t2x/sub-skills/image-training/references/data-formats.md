# Image Training Data Formats

## Purpose

Read this when you are preparing or validating image training data for the Lumina image branches.

## JourneyDB-style manifest

The repo's image trainers use a YAML file that points at one or more JSON or JSONL manifest files.

### YAML shape

```yaml
META:
  -
    path: '/path/to/journeyDB_train.json'
    root: '/path/to/image_folder'
    type: default
    ratio: 1.0
```

### Field meaning

- `path`: JSON or JSONL manifest file.
- `root`: optional directory that is joined onto `path`, `image`, or `image_url` values.
- `type`: optional grouping label; defaults to `default`.
- `ratio`: optional deterministic sample ratio for downsampling a large manifest.

## JSON manifest item

A common item shape is:

```json
{
  "conversations": [
    {"from": "user", "value": ""},
    {"from": "gpt", "value": "a caption for the image"}
  ],
  "image": "relative/or/absolute/image.jpg"
}
```

### Notes

- The data loader supports both `.json` and `.jsonl`.
- `image`, `image_url`, or `path` fields are eligible for `root` prefix joining.
- The `conversations` layout is the canonical image-caption structure in the README examples.

## Cache behavior

- When `--cache_data_on_disk` is enabled, the training code writes an `accessory_data_cache/` directory derived from the config path.
- If the underlying manifest changes, the cache must be deleted or the old data may be reused silently.

## DreamBooth / mini adaptation inputs

The SD3 DreamBooth path uses a data directory plus an `instance_prompt` and may also use a local diffusers model root when offline.

## Validation intent

The bundled training-data checker should confirm:

- YAML parses and contains `META`.
- Each manifest file exists.
- The first few manifest items contain the expected caption/image fields.
- Joined image paths resolve under the declared root when one is supplied.
