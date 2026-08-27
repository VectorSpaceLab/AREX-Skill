# Publishable Asteroid models

## Local publishable artifact contract

`save_publishable(publish_dir, model_dict, metrics=None, train_conf=None, recipe=None)` expects `model_dict` to include:

- `model_args`
- `state_dict`
- `dataset`
- `licenses`
- `infos`

It then saves a `model.pth` file in `publish_dir`.

## Required metadata for upload preparation

The model metadata is enriched with:

- uploader name
- affiliation
- git username
- upload name
- license notice
- recipe name
- training config
- final metrics

## Upload helper behavior

`upload_publishable(...)`:

- loads the local `model.pth`
- populates uploader metadata
- requires a Zenodo token unless `ACCESS_TOKEN` is already set
- supports sandbox uploads
- can return a unit-test-friendly metadata object when `unit_test=True`

## Sample-rate registration

`asteroid-register-sr` exists for older checkpoints that were saved before `sample_rate` was included.

It edits the serialized checkpoint in place by adding the missing sample-rate field.

## Safe smoke path

A good local smoke check is to:

1. build a tiny model
2. call `serialize()`
3. attach dataset/license metadata
4. call `save_publishable(...)`
5. inspect the generated `model.pth`

Do not do a real upload unless the caller explicitly wants that step and has credentials available.
