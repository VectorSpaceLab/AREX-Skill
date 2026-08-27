# Specialty CLI Reference

This reference records the inspected installed entry points. Use the entry
point names, not Python files in a checkout. Every command that uses
`add_merge_options` accepts the shared options below in addition to its own
arguments.

## Shared merge options

The following surface is available on `mergekit-pytorch`, `mergekit-multi`,
`mergekit-moe`, `mergekit-extract-lora`, `mergekit-tokensurgeon`,
`mergekit-layershuffle`, and `mergekit-legacy`:

### Dangerous and storage

```text
--allow-crimes / --no-allow-crimes
--trust-remote-code / --no-trust-remote-code
--transformers-cache TEXT
--lora-merge-cache TEXT
--lora-merge-dtype TEXT
```

`--allow-crimes` permits mixed architectures and is off by default. It is not a
shape or semantic compatibility proof. `--trust-remote-code` executes model
repository code and is off by default. The cache options change where model or
LoRA material is stored; they do not make a remote reference offline.

### Miscellaneous

```text
--random-seed INTEGER
-v                         # repeat for more verbosity
--quiet / --no-quiet
```

### Performance

```text
--cuda / --no-cuda
--device TEXT
--low-cpu-memory / --no-low-cpu-memory
--lazy-unpickle / --no-lazy-unpickle
--read-to-gpu / --no-read-to-gpu
--multi-gpu / --no-multi-gpu
-j, --num-threads INTEGER
--gpu-rich                  # --cuda --low-cpu-memory --read-to-gpu --multi-gpu
--async-write / --no-async-write
--write-threads INTEGER
```

### Output settings

```text
--out-shard-size SIZE
--copy-tokenizer / --no-copy-tokenizer
--clone-tensors / --no-clone-tensors
--write-model-card / --no-write-model-card
--safe-serialization / --no-safe-serialization
```

Defaults observed in help are: no CUDA, no low-CPU-memory, no lazy unpickle,
no direct-read-to-GPU, no multi-GPU, one write thread, `5B` output shard size,
copy tokenizer, no tensor cloning, write model card, and safe serialization.
`--async-write` trades memory for write speed. Do not use `--gpu-rich` merely to
make a command appear faster; first use the resource route in
`../model-io-and-architecture/SKILL.md`.

## `mergekit-pytorch`

```text
mergekit-pytorch [OPTIONS] CONFIG_PATH OUT_PATH
```

Required positional inputs are an existing raw YAML file and an output path.
The YAML model entries must point to local PyTorch pickle/`.pt` or
safetensors files (the command's documented raw input contract); use
`merge_method`, `models`, optional per-model `parameters`, optional global
`parameters`, optional `dtype`, and optional `base_model`. Raw configs are
similar to mergekit YAML but do **not** support `slices` or tokenizer
configuration.

Special options:

```text
-i, --tensor-intersection    only tensors present in every input model
-u, --tensor-union           tensors present in any input model
```

With neither flag, a tensor missing from any participating input is an error.
Intersection skips non-common tensor names. Union retains names seen in any
input, but the selected merge method must still tolerate missing inputs and
all participating tensors must have compatible shapes for the operation.
If both flags are supplied, the inspected planner checks intersection first;
do not rely on that accidental precedence—choose one explicitly. Output is a
checkpoint directory written with the shared shard/serialization settings.

## `mergekit-multi`

```text
mergekit-multi [OPTIONS] CONFIG_FILE
  --out-path PATH
  -I, --intermediate-dir PATH
  --lazy / --no-lazy
```

`--intermediate-dir` is required. `--out-path` is required when the YAML stream
contains an unnamed final document. The file is a YAML multi-document stream;
each named document becomes an intermediate model under
`INTERMEDIATE_DIR/<name>`, and one unnamed document becomes the final model at
`--out-path`. Standard mergekit options apply to the inner merges.

`--lazy` (default) skips an intermediate when its output contains
`config.json` and a recognized model checkpoint marker; `--no-lazy` reruns it.
Names are unique and references to a prior name are replaced with paths under
the intermediate directory. A dependency cycle stops with a circular
dependency error. An unresolved name is not a valid model path: stop and fix
it instead of allowing a Hub lookup or a confusing loader failure.

## `mergekit-moe`

```text
mergekit-moe [OPTIONS] CONFIG_PATH OUT_PATH
```

Special options:

```text
--load-in-4bit
--load-in-8bit
--i-understand-this-is-not-useful-without-training
```

The last flag explicitly permits the all-identical-expert case; it is not a
quality switch. See [moe.md](moe.md) before using it.

## `mergekit-extract-lora`

This command has no positional arguments; all three model/output inputs are
required options:

```text
mergekit-extract-lora [OPTIONS]
  --model TEXT                 required fine-tuned model
  --base-model TEXT            required base model
  --out-path TEXT              required adapter output
  --max-rank INTEGER
  --distribute-scale / --no-distribute-scale
  --embed-lora / --no-embed-lora
  --save-module TEXT           repeatable
  -e, --exclude-regex TEXT     repeatable
  -i, --include-regex TEXT     repeatable
  --sv-epsilon FLOAT
  --skip-undecomposable
```

The inspected default maximum rank is 128, scale distribution is enabled,
embedding LoRA is disabled, and singular-value threshold is 0. The output is a
PEFT-compatible adapter directory, normally including `adapter_model` shards,
`adapter_config.json`, and a generated `README.md`. Do not overwrite a base
model directory with this output.

## `mergekit-tokensurgeon`

```text
mergekit-tokensurgeon [OPTIONS] MODEL DONOR OUT_PATH
```

The base/model reference, donor tokenizer/model reference, and new output path
are required positionals. Specialty options are:

```text
-k, --k INTEGER
-c, --cosine-similarity / -nc, --no-cosine-similarity
-a, --approximation-method [common_interpolation|subword|mean|zero|randn|john_hewitt|omp|landmark_pca|stb|mp_rope]
-w, --weight-scheme [distance_proportional|barycentric|least_squares]
-s, --subword-method [mean|sum|weighted_mean|first_last]
--batch-size INTEGER
-pm, --prefix-match [lm_head|embed|yes|no]
-bm, --byte-match [lm_head|embed|yes|no]
--magikarp / --no-magikarp
-nvn, --new-vocab-noise FLOAT
-nvs, --new-vocab-scale FLOAT
```

The CLI defaults are `k=64`, Euclidean nearest-neighbor search, `omp`,
`distance_proportional`, `mean`, batch size 512, no prefix/byte matching, no
Magikarp filter, and no new-vocabulary noise or scale override. Shared device,
trust, cache, shard, and serialization flags also apply. The output is a copy
of the base architecture with donor tokenizer/config special-token metadata
and rebuilt input/output embeddings; it is not a LoRA or a conventional merge.

## `mergekit-layershuffle`

```text
mergekit-layershuffle [OPTIONS] OUT_PATH
```

Special options are repeatable where shown:

```text
-m, --model TEXT
-w, --weight FLOAT
--print-yaml / --no-print-yaml
--write-yaml PATH
--dry-run
--fp16 / --no-fp16
--full-random / --no-full-random
```

Supply at least one `--model`; weights are consumed in model order and should
match the model count. Without `--full-random`, the tool samples a source model
for each layer and coalesces adjacent layers from the same source. With
`--full-random`, it samples source and layer indices, builds a randomized
passthrough slice config, and shuffles the slices. `--print-yaml` prints the
config, `--write-yaml PATH` saves it, and `--dry-run` returns after generation
without calling the merge. Always use dry-run or write the YAML to a new path
before a real output path is permitted.

## Compatibility entry points

`mergekit-legacy OUT_PATH` accepts repeatable `--merge TEXT`, `--density FLOAT`,
`--weight FLOAT`, plus `--method TEXT` (default `ties`), `--base-model TEXT`,
`--normalize/--no-normalize`, `--int8-mask/--no-int8-mask`, `--bf16/--no-bf16`,
`--naive-count/--no-naive-count`, and `--print-yaml/--no-print-yaml`.
It translates a subset of old arguments into modern YAML. For `slerp`, exactly
one weight is required. Prefer `mergekit-yaml` and route method details to
`merge-configs`.

`bakllama CONFIG_PATH OUT_PATH` is a legacy layer-slice wrapper with
`--clone-tensors/--no-clone-tensors` and `--fp16/--no-fp16`. Its YAML contains
`layer_slices` entries (`model`, `start`, `end`, optional `scale`) and optional
`embedding_source`/`lm_head_source` fields. The inspected checkout's
`bakllama --help` is blocked by an import incompatibility, so treat this route
as unverified compatibility guidance: do not run it until the installed entry
point imports cleanly. It is not one of the verified first-class routes.

`mergekit-evolve` is intentionally outside this route. It belongs to
[extension-and-evolution](../../extension-and-evolution/SKILL.md), and the current
help probe is optional-blocked by missing `cma`.
