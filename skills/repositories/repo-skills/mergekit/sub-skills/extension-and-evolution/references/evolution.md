# Evolutionary merge search

## When to read this

Read this before planning `mergekit-evolve`. This is an optional, deprecated,
resource-heavy workflow, not a core mergekit smoke test. The safe default is a
configuration/dependency preflight only. Do not start CMA-ES, Ray, LM-Eval,
vLLM, W&B, model downloads, or large merges merely to verify installation.

## Dependency gate

MergeKit 0.1.4 declares evolutionary support in an optional `evolve` extra:
`ray`, `cma`, `lm_eval`, and `wandb`. The optional `vllm` extra adds the pinned
vLLM integration and `lm_eval[vllm]`. These are not base dependencies.

The installed inspection snapshot had all five optional modules absent. In
that state, `mergekit-evolve --help` fails during module import with
`ModuleNotFoundError: cma`, before Click parses `--help`; the strategy module
also imports Ray and LM-Eval. Record this as an explicit optional-dependency
gate, not as a missing core MergeKit feature. A safe preflight can report
availability without importing the optional modules:

```sh
python - <<'PY'
import importlib.util
for name in ("cma", "ray", "lm_eval", "wandb", "vllm"):
    print(f"{name}: {'available' if importlib.util.find_spec(name) else 'missing'}")
PY
```

Install only the extras needed for an approved experiment. Recheck the
PyTorch/CUDA/vLLM compatibility matrix after installing vLLM; it can alter an
otherwise working accelerator environment. Do not place credentials, caches,
private paths, or service tokens in a skill or a committed config.

## Evolution configuration

The positional argument is a YAML genome configuration. Its two required
sections are `genome` and `tasks`:

```yaml
genome:
  models:
    - model-a
    - model-b
  merge_method: linear
  base_model: null
  tokenizer_source: null
  layer_granularity: 0
  normalize: null
  allow_negative_weights: false
  filters: null
  smooth: false
tasks:
  - name: my_eval_task
    weight: 1.0
    metric: acc,none
```

### Genome fields

- `models`: a non-empty list of model references available to the search.
- `merge_method`: one of the version-backed methods `linear`,
  `task_arithmetic`, `ties`, `dare_ties`, or `slerp`.
- `base_model`: optional for linear/slerp, but required by the genome validator
  for `task_arithmetic`, `ties`, and `dare_ties`.
- `tokenizer_source`: optional tokenizer donor passed into generated merge
  configurations.
- `layer_granularity`: `0` uses one parameter group; a positive value creates
  one group per consecutive layer block and must divide the input model's
  layer count exactly. Larger blocks shrink the search space but reduce
  per-layer flexibility.
- `normalize`: optional override. If omitted, the current genome defaults it
  to true for `linear`, `ties`, and `dare_ties`, and false for the other
  supported methods.
- `allow_negative_weights`: defaults false. When false, weight/t interpolation
  values are made non-negative; task-arithmetic variants usually need true when
  negative task vectors are intended.
- `filters`: optional tensor-name filter list. Each filter adds a parameter
  group plus an unfiltered group, increasing the genome dimension.
- `smooth`: interpolates parameters across layers for supported methods. It is
  incompatible with `slerp`; `slerp` also rejects `filters`.

The genome parameter map is fixed in this release: `linear` and
`task_arithmetic` search `weight`; `ties` and `dare_ties` search `weight` and
`density`; `slerp` searches `t`. Density is clamped to `[0, 1]` in the generated
merge configuration. SLERP selects the two highest-weight models per layer
group and converts them to an interpolation `t`.

### Evaluation tasks

Each task may be a string (shorthand for `name`) or an object:

```yaml
tasks:
  - name: custom_task
    weight: 1.0
    metric: acc,none
```

`weight` defaults to `1.0`; `metric` defaults to `acc,none`. The aggregate
objective is the weighted sum of the named metrics, and the optimizer negates
that score because CMA-ES minimizes. Give a lower-is-better metric such as
perplexity a negative task weight. The task must actually be available to
LM-Eval; use `--task-search-path` repeatedly for custom task directories.

Top-level evaluation controls are `limit`, `num_fewshot`, `shuffle`,
`random_init`, `apply_chat_template`, and `fewshot_as_multiturn`. Validate at
least one real task/metric pair before allocating GPUs. Do not optimize against
benchmark test sets casually: common benchmark prefixes are rejected unless
the explicit benchmark-acknowledgement flag is supplied.

## Command contract and bounded controls

The command shape is:

```sh
mergekit-evolve [OPTIONS] --storage-path PATH GENOME_CONFIG_PATH
```

Important controls in 0.1.4:

| Option | Default/meaning | Safe planning note |
|---|---|---|
| `--max-fevals` | `100` | Maximum requested evaluations; CMA-ES may exceed it by roughly one generation (the package documents up to about 50%). Set a small pilot budget only after a valid evaluator exists. |
| `--sigma0` | `1/6` | Initial CMA-ES sigma; keep the default unless the search space and scaling justify a change. |
| `--force-population-size` | unset | Optional CMA-ES population override; larger populations increase cost per generation. |
| `--timeout` | unset | Wall-clock bound in seconds; use it with `--max-fevals` for an explicit stop condition. |
| `--random-seed` | `0` | Record it with model revisions, package versions, and evaluator settings for reproducibility. |
| `--storage-path` | required | Shared location for resharded inputs, caches, candidate merges, and the best config; budget at least one fp16 model per GPU for on-disk operation. |
| `--strategy` | `pool` | Choose `pool`, `buffered`, or `serial` only after matching storage and GPU topology. |
| `--batch-size` | unset | Evaluation batch size; vLLM commonly uses `auto`. |
| `--num-gpus` | detected accelerator count | Override only when the Ray-visible GPU count and merge device agree. |
| `--merge-cuda/--no-merge-cuda` | enabled | GPU merge controls are separate from evaluator backend placement; use the CPU flag only when the rest of the run is CPU-compatible. |
| `--vllm/--no-vllm` | disabled | Requires the optional vLLM/LM-Eval integration; do not enable by default. |
| `--in-memory/--no-in-memory` | disabled | Pool-only in the strategy implementation; it mutates evaluator model internals and is explicitly fragile. |
| `--wandb/--no-wandb` | disabled | Requires `wandb`, a project/entity decision, network access, and credentials. |
| `--task-search-path` | repeatable | Adds custom LM-Eval task search roots. |
| `--trust-remote-code` | disabled | Enable only for trusted model code and record the decision. |
| `--allow-crimes` | disabled | Preserve as an explicit architecture/trust decision; route core model-risk details to the sibling architecture skill. |
| `--reshard/--no-reshard` | enabled | Reshards inputs to single-file safetensors and consumes extra storage; disable only with a known compatible layout. |
| `--save-final-model/--no-save-final-model` | enabled | Final merge is another large write; disable for a config-only pilot. |
| `--load-in-4bit`, `--load-in-8bit` | disabled | Mutually exclusive, incompatible with vLLM and in-memory mode, and require `bitsandbytes`. |

The command is deprecated in this release and may be removed in a future
version. Pin the package and preserve the exact YAML/CLI invocation if the
result matters.

## Scheduling strategies

### `pool`

`ActorPoolEvaluationStrategy` creates one Ray merge/evaluation actor per
available GPU. It keeps a candidate's merge and evaluation together on the
actor's node. It is the documented safe default for local or distributed
clusters. On-disk actors use the compatibility-first path. In-memory mode is
available only in this strategy, avoids repeated disk writes, and is fragile
because it patches LM-Eval/vLLM/Transformers internals; use it only as a
measured experiment.

### `buffered`

`BufferedRayEvaluationStrategy` maintains merge and evaluation queues to keep
GPUs occupied. It is on-disk only: the implementation rejects in-memory mode.
Use it for a single node or when `storage-path` is a fast filesystem shared by
all relevant nodes. It can overlap merge/evaluation work and therefore needs
more VRAM and careful storage sizing.

### `serial`

`SerialEvaluationStrategy` submits each genotype through a Ray placement group
that packs one CPU and one GPU, keeping merge and evaluation together. It also
rejects in-memory mode. It is a troubleshooting fallback, not an automatic
performance choice; confirm that Ray sees the requested accelerator and that
one-GPU placement is valid.

## On-disk, in-memory, and output paths

On-disk mode is the compatibility-first path: merge a genotype to a temporary
candidate under the storage root, evaluate it, then clean up the candidate.
The root also holds resharded input models and transformer/LoRA caches. The
best-so-far configuration is written as `best_config.yaml`; if enabled, the
final model is written under `final_model`.

In-memory mode keeps one model resident and applies planned tensor results
through the graph executor. It saves disk and model reload time but depends on
private integration points in LM-Eval/vLLM and may fail after dependency
updates. It is not supported by buffered or serial strategies. Treat it as an
experimental optimization with a rollback to on-disk pool mode.

Do not share a storage root between unrelated runs without a deliberate naming
scheme. Preserve the genome YAML, model revisions, generated
`best_config.yaml`, CLI options, seed, evaluator task files, GPU count, and
package/extra versions as the reproducibility record.

## GPU and evaluator planning

Before any run, prove all of the following:

1. Ray, PyTorch, and the selected merge device report the same usable GPU
   count; `--num-gpus` is not a substitute for physical or Ray visibility.
2. The selected strategy's placement model matches the filesystem topology.
3. The model architecture, dtype, shard size, and batch size fit the available
   memory. Route architecture conversion, model references, and general device
   planning to `model-io-and-architecture`.
4. LM-Eval can discover every configured task and metric using the selected
   task search path.
5. vLLM is installed and compatible only when `--vllm` is selected; otherwise
   use the Hugging Face evaluator backend.
6. W&B is disabled unless network access, credentials, project, and entity
   ownership have been explicitly approved.

A safe pilot is a config-only validation plus optional-module check. Only after
that approval should a contributor choose a tiny model fixture, a tiny task
limit, bounded `--max-fevals`, bounded `--timeout`, and a disposable storage
root. Full model evaluation is never a default verification action.
