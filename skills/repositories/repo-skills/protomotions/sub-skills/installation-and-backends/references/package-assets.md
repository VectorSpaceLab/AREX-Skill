# Package and asset behavior

## What an installed distribution provides

A package install provides the `protomotions` Python package, console entry points, and package data declared by metadata. Robot assets under the package's `data/assets` tree are included except for explicitly excluded SMPL/SMPL-H assets.

A package install does **not** necessarily include:

- source-checkout examples and tutorials;
- large pretrained checkpoints;
- packaged MotionLib `.pt` files;
- media assets;
- conversion helper scripts outside the Python package;
- SMPL/SMPL-H body-model assets that require separate license terms.

When a task needs those artifacts, require either user-provided paths or a source checkout with Git LFS files materialized.

## Asset resolution

ProtoMotions resolves assets through `protomotions.assets`:

- `DEFAULT_ASSET_ROOT` is the portable config value `protomotions/data/assets`.
- `get_asset_root()` returns `PROTOMOTIONS_ASSET_ROOT` if set and valid; otherwise it resolves the installed package's `data/assets` directory.
- `resolve_asset_root()` preserves explicit non-default roots so wrong paths fail loudly instead of silently falling back.
- `asset_path()` raises if a requested asset is missing and explains the SMPL/SMPL-H carve-out.

## Practical checks

```bash
protomotions info --json
```

Inspect:

- `asset_root`: where runtime assets resolve.
- `asset_root_override`: whether `PROTOMOTIONS_ASSET_ROOT` is controlling resolution.
- `assets.mjcf`, `assets.urdf`, `assets.usd`, `assets.mesh`: whether expected subtrees exist.
- `simulators`: import availability for backend modules.

## Git LFS and large artifacts

If using a source checkout for pretrained models or example motions, verify that Git LFS files are not pointer files. A pointer file starts with `version https://git-lfs.github.com/spec/v1` and can trigger confusing simulator or checkpoint errors.

## SMPL/SMPL-H licensing

SMPL and SMPL-H assets are excluded from built artifacts. Do not work around this by copying them into a public wheel or generated skill. Ask the user to provide a licensed local asset root and set `PROTOMOTIONS_ASSET_ROOT`.
