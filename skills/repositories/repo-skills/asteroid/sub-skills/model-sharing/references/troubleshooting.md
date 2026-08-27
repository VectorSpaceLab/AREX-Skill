# Model sharing troubleshooting

## Missing metadata keys

- `save_publishable(...)` asserts that the model dict includes the required keys.
- If a save fails, inspect the checkpoint dict before trying again.

## Missing token or credentials

- `upload_publishable(...)` needs a Zenodo token.
- Use `ACCESS_TOKEN` or pass `--token` explicitly.
- Real uploads are credential-bound and should not be used as a default smoke check.

## Publish vs. inspect

- `unit_test=True` is for safe metadata inspection only.
- `force_publish=True` skips the final confirmation and should be used only when the user explicitly wants publication.

## Local checkpoint load checks

- PyTorch 2.6+ defaults `torch.load(..., weights_only=True)`, which can reject trusted Asteroid publishable smoke artifacts containing objects such as `TorchVersion`.
- For a file you just created locally and trust, use `torch.load(path, map_location="cpu", weights_only=False)` for the smoke check.
- Do not use `weights_only=False` for untrusted downloaded checkpoints.

## Legacy checkpoints

- `asteroid-register-sr` only applies to old serialized checkpoints that were saved without `sample_rate`.
- Do not use it on a modern checkpoint unless you have a specific compatibility reason.

## Network issues

- Zenodo and Hugging Face interactions are network-dependent.
- If the user only needs a local publishable artifact, keep the workflow offline.
