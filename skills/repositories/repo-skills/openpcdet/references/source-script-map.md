# Source Script Map

This skill wraps or distills OpenPCDet checkout scripts instead of linking to the construction checkout.

## Wrapped by bundled helpers

| Source workflow | Bundled helper | Treatment | Reason |
|---|---|---|---|
| Train workflow script | `scripts/plan_openpcdet_command.py --mode train` | Wrapped | Provides checked command construction and optional execution for any checkout. |
| Test/evaluation workflow script | `scripts/plan_openpcdet_command.py --mode test` | Wrapped | Captures `--ckpt`, `--eval_all`, `--save_to_file`, distributed launcher, and output semantics. |
| Demo workflow script | `scripts/plan_openpcdet_command.py --mode demo` plus `sub-skills/inference-and-custom-data/scripts/check_point_cloud_array.py` | Wrapped/adapted | Adds safe point-cloud validation and explicit checkpoint/config/data coupling. |
| Dataset info entrypoints | `scripts/plan_openpcdet_command.py --mode <dataset>-infos` plus `sub-skills/data-preparation/scripts/check_openpcdet_dataset_layout.py` | Wrapped | Dataset conversion can be expensive; helper prints commands by default and layout checker is non-destructive. |
| Config loading | `scripts/summarize_openpcdet_config.py` | Adapted | Uses `pcdet.config` loader to summarize YAML without building datasets/models. |
| Registry/config inventory | `sub-skills/models-and-configs/scripts/inventory_openpcdet_configs.py` | Adapted | Produces an operator inventory across YAML configs and registries. |
| Runtime/native import checks | `scripts/inspect_openpcdet_runtime.py` | Adapted | Provides import and CUDA-extension diagnostics without running native examples. |

## Reference-only source scripts

| Source workflow | Reason not copied verbatim |
|---|---|
| Shell launchers for distributed/SLURM train/test | They are thin wrappers around train/test with machine-specific GPU counts, partition names, and environment assumptions. Their semantics are captured in `training-and-evaluation` references and the command builder. |
| Dataset module `__main__` blocks | They are tightly coupled to dataset roots and generated file names. The skill documents command shapes and bundles layout checks instead of copying large converters. |
| `tools/process_tools/create_integrated_database.py` | Useful for advanced database aggregation but specialized and data-heavy; documented as an advanced reference-only workflow. |
| Visualization utility modules | They depend on optional Open3D/Mayavi GUI stacks. The inference sub-skill explains routing and non-visual adaptation instead of copying visualization code. |
| Native CUDA extension source files | They are build artifacts of the package, not scripts for future operators. Runtime verification uses import probes rather than copying extension sources. |
