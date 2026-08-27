# Plugin and config discovery contract

AlpaSim discovers installed extensions through Python packaging entry points.
The registry is lazy and name-based; it does not scan arbitrary directories or
load models from a source checkout.

## Supported groups

| Entry-point group | Meaning |
|---|---|
| `alpasim.models` | Trajectory model class/factory; the driver calls `from_config` |
| `alpasim.mpc` | MPC controller implementation |
| `alpasim.scorers` | Evaluation scorer |
| `alpasim.tools` | CLI/tool extension |
| `alpasim.configs` | Hydra config package added to the wizard search path |

The safe inspection command is `alpasim-info`. The bundled helper in
`scripts/check_driver_plugins.py` can show distribution, entry-point value, and
optional import errors without instantiating a model or downloading weights.
`PluginRegistry.get(name)` raises `PluginNotFoundError` with the available names
when a name is absent. During discovery, an entry point that cannot import is
warned about and omitted; inspect warnings instead of assuming the package is
healthy.

## Minimal model plugin pattern

A model package should depend on `alpasim_plugins` and on the distribution that
defines its interface (`alpasim_driver` for `BaseTrajectoryModel`). Its
`pyproject.toml` needs an entry point like:

```toml
[project.entry-points."alpasim.models"]
my_policy = "my_package.model:MyPolicy"
```

`MyPolicy` must implement the common model interface and preserve the rig-frame
contract. It should validate camera IDs and frame counts before inference, keep
weights external, and avoid import-time checkpoint downloads. Register a name
that does not collide with a built-in or another installed plugin.

## Config package pattern

A plugin that ships Hydra configs exposes a Python package containing the YAML
config groups and registers:

```toml
[project.entry-points."alpasim.configs"]
my_policy = "my_package.configs"
```

The wizard discovers this group and adds the package to Hydra's search path.
Do not add a manual `hydra.searchpath` override for a normally installed
plugin. Keep config group paths consistent with the selected group, for
example a `driver/my_policy.yaml` file is selected as `driver=my_policy`.
The config's `model.model_type` must exactly match the model entry-point name.

## Transfuser as the complete example

The optional Transfuser distribution registers both:

```toml
[project.entry-points."alpasim.models"]
transfuser = "alpasim_transfuser.transfuser_model:TransfuserModel"

[project.entry-points."alpasim.configs"]
transfuser = "alpasim_transfuser.configs"
```

Its config selects `model_type: transfuser`, `device: cuda`, four cameras in a
specific left/front/right/rear order, `max_batch_size: 16`,
`subsample_factor: 1`, and a checkpoint path whose directory also contains
`config.json`. The adapter requires exactly one frame per camera, resizes each
to 270x480, concatenates horizontally in the configured order, one-hot encodes
the route command, and passes speed and acceleration. It converts CARLA's
positive-right y convention to AlpaSim's positive-left rig convention before
returning the plan. Do not use a single-camera video-model preset for this
plugin.

## Registration/config mismatch diagnosis

When `driver=transfuser` fails but `alpasim-info` has no Transfuser model or
config, first verify the plugin distribution is installed in the same Python
environment that runs the wizard. Then inspect both entry-point groups:

```bash
python scripts/check_driver_plugins.py --group alpasim.models
python scripts/check_driver_plugins.py --group alpasim.configs
```

If the model entry point is present but the config group is absent, install or
repair the package metadata and reinstall the plugin; do not patch the core
wizard search path. If the config is present but `model_type` is not, repair the
YAML name. If the entry point is present but import fails, resolve the reported
optional dependency first. Only after both groups are visible should you debug
checkpoint paths or camera contracts.

Plugins extend the available set; they are not a supported override mechanism
for replacing built-ins. Keep the interface dependency direction generic:
plugin code may depend on the driver API, but generic core modules must not
import a concrete plugin.
