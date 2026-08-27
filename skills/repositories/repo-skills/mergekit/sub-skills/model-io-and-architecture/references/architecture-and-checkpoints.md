# Architecture and checkpoint handling

## 1. Establish a model identity before inspecting tensors

Represent a source as one of these forms:

```text
org/model
org/model@immutable-or-explicit-revision
/local/model-directory
/local/model-directory@revision   # syntactically accepted, but revisions are normally Hub metadata
org/model+org/adapter
org/model@rev+org/adapter@adapter-rev
```

`ModelReference.parse` splits at `+` first and validates each `ModelPath`. Each
path accepts at most one `@`; `@@@@@`, `a+b+c`, and similar malformed strings
raise `RuntimeError`. A local path is not made valid by adding a revision: verify
that its `config.json` and checkpoint files are present. A Hub path is resolved
with the requested revision. Keep the exact reference in the run record because
it controls cache identity, architecture config, and reproducibility.

A LoRA reference is an adapter to be merged, not an additional model tensor
source. `ModelReference.merged()` requires `lora_merge_cache`; it chooses the
base architecture, loads the base with a Transformers auto class, applies PEFT,
merges and unloads, and saves a safe-serialized cached model. If the adapter is
not intended to be merged, stop and route the request to the specialty workflow.
Do not bypass the assertion in `local_path()` by ignoring an unmerged LoRA in a
normal merge.

`trust_remote_code` defaults to false. Enabling it can execute/import Python
from a remote model repository while loading config, model, or tokenizer. Record
who supplied the repository, the exact revision, and why the code is trusted;
prefer a reviewed local mirror. `allow_crimes` is a separate, dangerous choice:
it permits known architecture objects to differ, but it does not convert tensor
names, validate shapes, or make a mathematically meaningful merge.

## 2. Select and validate the output architecture

The architecture route follows this order:

1. Load each referenced model's `PretrainedConfig` with the effective
   `trust_remote_code` policy.
2. Read the one expected name in `config.architectures`. More than one name is a
   runtime error in `arch_info_for_config`.
3. Match the name against the package's bundled JSON architecture resources. If
   several definitions share a name, prefer one whose expected `model_type`
   equals the config's `model_type`.
4. Handle the explicit AFMoE and GLM4-MoE architecture classes when their
   architecture names match.
5. If any model has no known definition, call auto inference across the set of
   references (and `base_model` when present).
6. If every model is known but the resulting objects differ, refuse unless
   `allow_crimes` is true. Even with the flag, continue to compare layer count,
   module prefixes, weight names, shapes, dtypes, embeddings, and tied weights.

A `ModelArchitecture` contains `modules`, accepted architecture names, an
expected model type, optional tagalong files, and an optional vocabulary-size
config key. Each `ModuleDefinition` can add a weight prefix and a subfolder.
`ConfiguredModelArchitecture.all_weights()` and
`ConfiguredModuleArchitecture.{pre_weights,layer_weights,post_weights}` turn
that description into concrete `WeightInfo` objects for one config.

## 3. Read bundled JSON definitions correctly

A module JSON definition has these effective fields:

- `model_type`: expected Transformers model type.
- `architectures`: accepted `config.architectures` names.
- `pre_weights`: tensors before the repeated layers.
- `layer_templates.weights`: names containing `${layer_index}` when repeated.
- `post_weights`: tensors after the layers.
- `num_layers_config_key`: dotted config key for the layer count.
- `override_num_layers`: a fixed count used by inferred definitions.

A modular definition additionally maps module names to definitions and may carry
`weight_prefix`, `subfolder`, `tagalong_files`, and `vocab_size_config_key`.
Template substitution supports `${num_layers}`, `${num_layers+1}`,
`${num_layers-1}`, and layer-index forms such as `${layer_index+1}`. The
substitution is performed against the output or input config when the configured
architecture is bound.

`WeightInfo` is the checkpoint contract, not merely documentation:

- `name` is the target/output name.
- `is_embed` lets the planner route the tensor through tokenizer permutation.
- `optional` permits a missing tensor in an input.
- `aliases` are alternate names tried before conversion.
- `tied_names` are additional candidates for tied weights.
- `force_dtype` applies a per-weight dtype.

For example, the Llama definition marks token embeddings as `is_embed`, makes
`lm_head.weight` optional, and ties it to `model.embed_tokens.weight`. Modern
MoE definitions expose packed expert targets such as
`model.layers.${layer_index}.mlp.experts.gate_up_proj`; an old checkpoint may
instead carry per-expert `w1`/`w3` or `gate_proj`/`up_proj` tensors.

Do not assume every JSON field is a universal API field. Use the installed
package's `WeightInfo` contract and treat architecture resources as data that
can change with the package version.

## 4. Understand auto inference and its limits

When no JSON definition is available, `infer_architecture_info` inventories
checkpoint tensor names through `LazyTensorLoader`. It optionally creates a
Transformers model on the `meta` device (without materializing weights) to
obtain:

- state-dict names in the current Transformers layout,
- input/output embedding names,
- ignored-on-save keys, and
- tied-weight keys when the installed Transformers exposes the helper.

Layer names are recognized by a numeric component surrounded by dots. Inferred
modules are formed from prefixes; a single prefix is collapsed into the
`default` module. Repeated templates become `${layer_index}` definitions and
loose names become pre-weights. `override_num_layers` records the count observed
in the checkpoint. A template is optional if a required target cannot be
produced by every referenced input, or if it is tied/ignored according to the
available model metadata.

Inference can be incomplete when config loading, model construction, meta
instantiation, or a compatible Transformers auto class fails. In that case the
route falls back to raw checkpoint names and loses tied/ignored/embed evidence.
Treat the warning as a verification gap. Do not infer a cross-family merge from
matching superficial prefixes alone.

## 5. Checkpoint names and conversion

`LoadTensor` resolves a target in this order:

1. exact `WeightInfo.name`;
2. `aliases`;
3. `tied_names`;
4. `convert_checkpoint_tensors(model_type, source_tensors, target_key)` using
   the Transformers checkpoint conversion registry.

`can_convert_checkpoint_keys` is the cheap key-set predicate used during
inference. It returns true for an exact target, or when a registered sequence of
renames/combines can construct the target with complete wildcard groups. A
partial multi-source group returns false. This is important for expert-packed
weights: having only `w1` or having mismatched expert indices is not enough.

The conversion helper accepts tensors or zero-argument callables. Callables are
loaded only as transformations request them, which preserves lazy IO. It
returns a `torch.Tensor` or `None`; missing model type or missing conversion
mapping returns `None`. It is written for the Transformers v5 model layout, so
conversion direction must be checked against the installed Transformers
version.

Useful verified patterns include:

- `mixtral` old `block_sparse_moe.experts.{i}.w1/w3` pairs can form
  `model.layers.{layer}.mlp.experts.gate_up_proj` and old `w2` can form the
  packed target expected by the JSON architecture.
- `qwen3_moe` per-expert `gate_proj` and `up_proj` pairs can form
  `model.layers.{layer}.mlp.experts.gate_up_proj`.
- one-to-many mappings such as `hrm_text` can split a packed source into a
  target projection when the mapping says so.

These examples prove mapping mechanics, not arbitrary architecture compatibility.
After conversion, still compare tensor shape, dtype, expert count, layer index,
and semantic role. If conversion returns `None` for a required weight, stop with
the source model, target name, model type, available key pattern, and revision.

## 6. Plan tensor work and output config

`MergePlanner` first normalizes topology:

- top-level `models` become a model list in every architecture module;
- top-level `slices` become the sole module's slices and are rejected for
  multi-module architectures;
- module `models` become full-range input slices using each input module's layer
  count; a configured base model not already in the list is added as a full
  range.

It then emits one tensor task per output weight and layer. Input `WeightInfo`
objects are selected by corresponding source layer index. Optional weights are
skipped only when no input name, alias, or tied candidate exists. Embedding
weights are passed through tokenizer permutation when a tokenizer task exists;
that operation belongs to the configuration/tokenizer route, but this route must
ensure the architecture marks embeddings correctly.

`plan_to_disk()` builds `TensorWriterTask`, `SaveTensor`, `FinalizeModel`, and
possibly tokenizer tasks. `plan_in_memory()` produces `ReturnTensor` tasks. The
output config starts from `base_model` or the first referenced model, applies
`out_dtype` then `dtype` as a fallback for `torch_dtype`, and updates configured
layer-count keys from output slices. If no key can be updated, inspect the
warning and correct the output config manually.
