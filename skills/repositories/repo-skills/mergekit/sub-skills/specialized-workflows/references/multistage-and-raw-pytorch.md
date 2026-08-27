# Multi-stage and Raw PyTorch Workflows

## Raw `.pt` and safetensors merge

Choose `mergekit-pytorch` when the inputs are arbitrary checkpoint tensor
containers rather than model directories with a supported architecture. Create
a raw config like:

```yaml
merge_method: linear
models:
  - model: ./base.pt
    parameters:
      weight: 0.5
  - model: ./adapted.safetensors
    parameters:
      weight: 0.5
parameters: {}
dtype: float32
```

The inspected raw config contract is `merge_method`, a non-empty `models` list
whose entries have `model` and optional per-model `parameters`, optional global
`parameters`, optional `dtype`, and optional `base_model`. Do not add `slices`,
`tokenizer`, or `tokenizer_source`: raw planning is flat and tensor-name based.
Parameter expressions still belong to the selected merge method; use
[merge-configs](../../merge-configs/SKILL.md) for method-specific required
parameters and precedence.

Run:

```bash
mergekit-pytorch CONFIG_PATH OUT_PATH [--tensor-intersection | --tensor-union] [common options]
```

The command indexes every input and plans a task per tensor name. Default mode
requires every planned tensor to exist in every input/base tensor set. Use
`-i/--tensor-intersection` to skip names not present in all inputs. Use
`-u/--tensor-union` to retain names present in any input; this only makes
presence optional—the merge method may still require a tensor and tensor shape
compatibility is still required. Do not use both flags. A shape mismatch is not
repaired by either mode: stop, inspect the tensor names/shapes, and either
select a compatible checkpoint set or move to the architecture/IO route.

The output path is a tensor checkpoint directory written using
`--out-shard-size` and `--safe-serialization` (enabled by default). It does not
promise a Transformers `config.json` or tokenizer because the raw contract
contains neither. If a downstream loader needs those artifacts, stop and hand
off to [model-io-and-architecture](../../model-io-and-architecture/SKILL.md).
Use `--lazy-unpickle` only for trusted local pickle inputs; never treat pickle
files or `--trust-remote-code` as safe by default.

## Named multi-stage graph

Use `mergekit-multi` for one YAML file containing multiple `---` documents. A
named document is an intermediate; an unnamed document is the final. Example:

```yaml
name: first
merge_method: linear
models:
  - model: ./model-a
  - model: ./model-b
parameters:
  weight: 0.5
---
name: second
merge_method: slerp
base_model: first
models:
  - model: ./model-c
parameters:
  t: 0.5
---
merge_method: dare_ties
base_model: ./model-a
models:
  - model: second
    parameters:
      density: 0.6
      weight: 0.5
```

Run:

```bash
mergekit-multi CONFIG_FILE -I INTERMEDIATE_DIR [--out-path FINAL_DIR] [common options]
```

The `-I/--intermediate-dir` value is required. If the stream has an unnamed
final document, `--out-path` is required; with only named documents no final
path is needed. Named outputs are stored under the intermediate directory by
exact name. References can be a model string or a model-reference mapping, but
the reference must resolve exactly to one declared name to be an intermediate;
otherwise it is treated as an ordinary model reference and can trigger a
network/Hub lookup.

The tool discovers dependencies, topologically executes them, and patches a
named intermediate reference to its local output directory. `--lazy` (default)
skips a named output only when it has `config.json` plus a recognized checkpoint
marker; `--no-lazy` forces re-execution. The final unnamed document is not an
intermediate and is written to `--out-path`.

### Preflight and stop conditions

Before execution:

- Ensure every document is non-empty, every named document has a unique
  non-empty name, and there is at most one unnamed document.
- Build a dependency table from every `base_model` and model reference. Reject
  a missing intermediate name, self-reference, or cycle before the command.
- Use separate, new intermediate and final directories. Do not let a lazy cache
  hide a changed recipe; use `--no-lazy` after changing a document or its
  referenced source.
- Confirm each inner config through the core config route and each model path,
  architecture, device, and credential boundary through the IO route.
- Do not pass a name that happens to look like a Hub id when the intended
  dependency is local; an unresolved name can become an unexpected download.

A missing intermediate or cycle is a graph/configuration error, not a reason to
add `--allow-crimes` or `--trust-remote-code`. A completed earlier stage is
reusable only when its output checkpoint and configuration match the current
recipe and source provenance.
