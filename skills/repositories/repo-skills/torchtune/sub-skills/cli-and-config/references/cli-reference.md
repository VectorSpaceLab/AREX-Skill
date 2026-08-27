# torchtune CLI Reference

The `tune` console script is registered as `torchtune._cli.tune:main`. It exposes six subcommands: `download`, `ls`, `cp`, `run`, `validate`, and `cat`.

## CLI Map

| Task | Command | Notes |
| --- | --- | --- |
| Show help | `tune --help` or `tune <subcommand> --help` | The installed CLI is the source of truth for current options. |
| Download model files | `tune download <repo-id> [OPTIONS]` | Supports Hugging Face by default and Kaggle with `--source kaggle`. |
| List built-ins | `tune ls` | Prints recipe names and associated config names from the registry. |
| Copy built-in file | `tune cp <recipe-or-config> <destination> [--make-parents] [-n]` | Recipes copy as `.py`; configs copy as `.yaml`. |
| Inspect config | `tune cat <config-name-or-yaml> [--sort]` | Accepts built-in config names or local `.yaml`/`.yml` files. |
| Validate config | `tune validate <config-yaml>` | Checks `_component_` import/signature shape; may require optional deps. |
| Run recipe | `tune run [TORCHRUN-OPTIONS] <recipe> --config <config> [RECIPE-OPTIONS]` | Built-ins may be referred to by registry name; local recipes use paths. |

## Discovery And Copying

Start with the registry instead of importing recipe modules:

```bash
tune ls
python scripts/inspect_tune_registry.py --format table
python scripts/inspect_tune_registry.py --recipe lora_finetune_single_device --format json
```

Inspect or copy configs before editing:

```bash
tune cat llama2/7B_lora_single_device
tune cat llama2/7B_lora_single_device --sort
tune cp llama2/7B_lora_single_device ./configs/llama2_lora.yaml --make-parents
tune cp lora_finetune_single_device ./recipes/lora_finetune_single_device.py --make-parents
```

`cp` looks up names in the registry. If the destination suffix does not match the source type, torchtune appends `.py` for recipes or `.yaml` for configs. Use `-n`/`--no-clobber` when preserving local edits.

## `tune run` Argument Placement

The parser follows torchrun's shape:

```bash
tune run [TORCHRUN-OPTIONS] <recipe> --config <config> [key=value ...] [~field ...]
```

Correct distributed command:

```bash
tune run --nnodes=1 --nproc_per_node=4 \
  full_finetune_distributed \
  --config llama2/7B_full \
  output_dir=./runs/llama2-full epochs=1
```

Correct single-device command:

```bash
tune run lora_finetune_single_device \
  --config llama2/7B_lora_single_device \
  model.lora_rank=16 output_dir=./runs/lora-r16
```

Important placement rules:

- Torchrun options go before `<recipe>`. If there are no args before `<recipe>`, torchtune bypasses torchrun and uses direct `runpy` execution for built-ins.
- Recipe options go after the `--config <config>` pair and must be `key=value` overrides or `~field` removals.
- `--config` is required for `tune run`; omitting it is a parser error.
- Passing distributed options to a recipe whose registry entry has `supports_distributed=False` is a parser error.
- Local recipe files are converted to module dotpaths for distributed mode and run with `runpy.run_module`; built-in recipes are resolved to package recipe files internally.

## Built-In Versus Local Recipes

Use registry names for built-ins:

```bash
tune run full_finetune_distributed --config llama2/7B_full
```

Use paths for local recipe files and configs:

```bash
tune run my_recipes/custom_lora.py --config my_configs/custom_lora.yaml
```

A local recipe can pair with a built-in config name, and a built-in recipe can pair with a local config path. Do not import the `recipes` package directly; it is intentionally not a public import surface.

## Download Command

Hugging Face examples:

```bash
tune download meta-llama/Meta-Llama-3-8B-Instruct --output-dir ./models/llama3
tune download meta-llama/Meta-Llama-3-8B-Instruct --ignore-patterns '*.safetensors'
```

Kaggle examples:

```bash
tune download metaresearch/llama-3.2/pytorch/1b --source kaggle
```

Credential rules:

- For gated Hugging Face models, pass `--hf-token` or rely on a prior `huggingface-cli login`/`HF_TOKEN` environment value.
- For gated/private Kaggle models, pass `--kaggle-username` and `--kaggle-api-key` or use Kaggle-supported environment variables.
- Never write tokens into a reusable config, skill file, script, or shared shell history snippet.
- Kaggle downloads ignore `--output-dir` and `--ignore-patterns` because `kagglehub` does not support those options in this CLI path.

## Validation Choices

Use the cheapest check that answers the question:

```bash
python scripts/validate_config_shape.py ./my_config.yaml
python scripts/validate_config_shape.py ./my_config.yaml optimizer=bitsandbytes.optim.PagedAdamW8bit ~optimizer.fused
tune validate ./my_config.yaml
```

The bundled shape checker never launches training and can avoid component imports unless `--resolve-components` is set. `tune validate` loads the YAML and checks component imports/signatures; it can fail when optional packages for a selected component are not installed.
