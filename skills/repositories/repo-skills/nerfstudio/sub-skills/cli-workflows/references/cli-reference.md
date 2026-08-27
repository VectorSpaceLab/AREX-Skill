# Nerfstudio CLI reference

Use this as a command-routing reference. Every example is a command pattern, not a request to run a long job.

## Public command catalog

| Command | Use when | Safe preflight |
| --- | --- | --- |
| `ns-install-cli` | Install shell completion for installed `ns-*` commands. | Run `ns-install-cli --help`; do not mutate shell files without user approval. |
| `ns-process-data` | Convert raw captures into Nerfstudio datasets. | Run `ns-process-data --help`, then route to data-preparation. |
| `ns-download-data` | Download demo or benchmark datasets. | Run `ns-download-data --help`; downloads require network and disk. |
| `ns-train` | Train a built-in or registered method. | Run `ns-train --help`; route to training-and-configs. |
| `ns-viewer` | Load a completed run config into the web viewer. | Run `ns-viewer --help`; route to visualization-and-export. |
| `ns-eval` | Compute metrics from a completed run config. | Run `ns-eval --help`; route to visualization-and-export. |
| `ns-render` | Render a camera path, spiral, interpolation, or dataset output. | Run `ns-render --help`; route to visualization-and-export. |
| `ns-export` | Export point cloud, TSDF/Poisson/marching-cubes mesh, cameras, or Gaussian Splat PLY. | Run `ns-export --help`; route to visualization-and-export. |
| `ns-dev-test` and `ns-dev-sync-viser-message-defs` | Maintainer commands. | Do not use for ordinary package operation. |

## Tyro subcommand ordering

Nerfstudio CLIs use typed dataclass parsing. Optional arguments bind to the preceding subcommand, so placement matters.

Correct training shape:

```bash
ns-train {method} [method args] {dataparser} [dataparser args]
```

Examples:

```bash
ns-train nerfacto --data DATA_DIR
ns-train splatfacto --vis viewer nerfstudio-data --eval-mode filename
ns-train nerfacto --viewer.websocket-port 7010 --pipeline.datamanager.train-num-rays-per-batch 2048 --data DATA_DIR
```

Help follows the same rule:

```bash
ns-train --help
ns-train nerfacto --help
ns-train nerfacto nerfstudio-data --help
```

If a flag is ignored or rejected, move it after the method or dataparser that owns it and re-run `--help` at that level.

## Safe command discipline

- `--help` is safe for all public commands.
- `ns-download-data` performs network downloads; only run after confirming dataset, output directory, network, and disk.
- `ns-process-data` can copy/resize images and invoke external binaries; preflight first and route to data-preparation.
- `ns-train`, `ns-render`, `ns-eval`, `ns-export`, and `ns-viewer` can use GPU, load checkpoints, open services, or write artifacts; route to the focused workflow first.
