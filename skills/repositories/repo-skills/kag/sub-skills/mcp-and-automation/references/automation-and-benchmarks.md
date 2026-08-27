# Automation and Benchmarks

## Purpose

Read this when you need to submit a builder job, plan a benchmark run, or understand the shell workflow that stages benchmark configs.

## Distributed builder submission

`kag builder` posts a job request to an OpenSPG-backed cluster service.

Important flags from the source command:

- `--git_url` and `--commit_id` are required
- `--entry_script` points at the Python entry file to run inside the cloned source
- `--init_script` is optional and runs before the entry script
- `--validity_check` verifies that the scripts exist in the cloned repo before submission
- `--num_workers`, `--num_gpus`, `--gpu_type`, `--num_cpus`, `--memory`, `--storage`, `--image`, `--pool`, and `--env` shape the worker request

Use `--validity_check` before sending any live job request.

## Benchmark command surface

`kag benchmark` reads a benchmark job config file and can be used to drive builder/eval automation.

- `--job_config` selects the YAML file
- `--env` injects environment variables for the run

## Open benchmark shell workflow

The repo's benchmark shell workflow does three things:

1. rewrites values in `kag_config.yaml` from `env.json`
2. restores the project and commits the schema
3. runs the benchmark builder and eval scripts for the chosen dataset split

### Data-set naming

The shell workflow uses these dataset names:

- `all`
- `sub`
- `train`

### Command families in the shell workflow

- `build`
- `eval`
- `all`

## Planning guidance

Use the bundled benchmark planner instead of executing the live workflow when you only want to know what would happen.

The planner should summarize:

- config-file rewrite targets
- `knext project restore`
- `knext schema commit`
- builder and eval entry points
- checkpoint and result files that may be written
- any network, credential, or long-running side effects
