# Training configuration and CLI overrides

## Command shape

```bash
ns-train {method} [method args] {dataparser} [dataparser args]
```

If no dataparser subcommand is provided, Nerfstudio defaults to `nerfstudio-data` for many methods. Method options still belong after the method name.

## Common method-level options

```bash
ns-train nerfacto --data DATA_DIR
ns-train nerfacto --vis viewer+tensorboard --data DATA_DIR
ns-train nerfacto --viewer.websocket-port 7010 --data DATA_DIR
ns-train nerfacto --machine.num-devices 1 --data DATA_DIR
```

`--data` is an alias that sets the pipeline datamanager data path for the common case.

## Dataparser options

Dataparser options come after the dataparser name:

```bash
ns-train splatfacto --vis viewer nerfstudio-data --eval-mode filename --data DATA_DIR
```

Use this when explicit train/eval filename lists are in `transforms.json` or when a non-default dataparser needs its own flags.

## Config files and resume fields

- Training writes a `config.yml` inside the run output directory.
- Use `--load-dir OUTPUTS/.../nerfstudio_models` to continue/load model checkpoint weights during training.
- Use `--load-config OUTPUTS/.../config.yml` where the command supports loading a full saved config.
- Viewer/eval/render/export routes normally consume `--load-config`.

## Programmatic config edits

Public config objects are dataclasses. Important roots include `TrainerConfig`, pipeline configs, datamanager configs, dataparser configs, and model configs. In Python, edit the config before launching a train loop; do not mutate internals after `setup()` unless the code path documents it.

The test-backed reduced training strategy sets device to CPU, disables mixed precision and grad scaling, lowers iterations/rays/samples, and points the dataparser at tiny fixtures. Treat that as a smoke pattern, not a quality recipe.
