# API Reference (native checkout evidence)

These are reference facts about the separately provisioned native package, not
implementations supplied by this skill. Before inspecting native files, run
`cd <absolute-repo-root>` for `VLA_ADAPTER_REPO_ROOT`; the generated skill does
not provide loaders, action heads, projectors, or conversion code.

## Verified package facts

- Distribution: `vla-adapter` version `0.0.1`.
- Import package: `prismatic`.
- Public root exports include `available_models`, `available_model_names`, `conf`, `get_model_description`, `load`, `models`, `overwatch`, `util`, and `vla`.
- `prismatic.models` also exports `load_vla` and the component materializers used by the VLA workflows.

## Model loading

Verified signatures:

```python
load(model_id_or_path, hf_token=None, cache_dir=None, load_for_training=False, image_sequence_len=None)
load_vla(model_id_or_path, hf_token=None, cache_dir=None, load_for_training=False, step_to_load=None, model_type="pretrained", image_sequence_len=None)
```

Loader expectations:

| API | Local path expectation | Hub expectation | Notes |
| --- | --- | --- | --- |
| `load` | `config.json` plus `checkpoints/step-020792-epoch-01-loss=0.5268.pt` | `TRI-ML/prismatic-vlms/<model_id>/config.json` and `checkpoints/latest-checkpoint.pt` | Returns a `PrismaticVLM`. The local path is hard-wired to the exemplar checkpoint filename. |
| `load_vla` | A `.pt` file inside `checkpoints/`, with sibling `config.json` and `dataset_statistics.json` | `openvla/openvla-dev/<model_type>/<model_id>/checkpoints/step-*.pt` plus config/statistics assets | Returns an `OpenVLA`. `step_to_load` filters the remote checkpoint step. |

Other facts:

- `load_vla` reads `base_vlm` from `config.json` and can resolve a folder path stored in that field.
- `image_sequence_len` falls back to the config value when present, otherwise `1`.

## Action tokenization and heads

Verified signatures:

```python
ActionTokenizer(tokenizer, bins=256, min_action=-1, max_action=1, use_extra=False)
ActionTokenizer.__call__(action, use_minivlm)
ActionTokenizer.decode_token_ids_to_actions(action_token_ids)
L1RegressionActionHead(input_dim=4096, hidden_dim=4096, action_dim=7, num_task_tokens=512, use_pro_version=False)
ProprioProjector(llm_dim, proprio_dim)
NoisyActionProjector(llm_dim)
```

Notes:

- `ActionTokenizer` discretizes continuous actions into the last `n_bins` tokens of the tokenizer vocabulary.
- `ActionTokenizer.__call__` returns token ids when `use_minivlm=True`; otherwise it returns decoded token strings.
- `use_extra=True` is only supported for `Qwen2TokenizerFast`; other tokenizers raise `NotImplementedError`.
- `L1RegressionActionHead` is the continuous-action path used by the finetuning and deployment flows.
- `ProprioProjector` feeds proprioceptive state into the LLM embedding space.
- `NoisyActionProjector` is the diffusion-style action conditioning path.

## Robot and token constants

| Platform | Action chunk | Action dim | Proprio dim | Normalization |
| --- | ---: | ---: | ---: | --- |
| LIBERO | 8 | 7 | 8 | `bounds_q99` |
| CALVIN | 8 | 7 | 8 | `bounds_q99` |
| ALOHA | 25 | 14 | 14 | `bounds` |
| BRIDGE | 5 | 7 | 7 | `bounds_q99` |

Additional verified constants:

- `ROBOT_PLATFORM` is inferred from command-line text and defaults to `LIBERO` when no platform word is present.
- `ACTION_TOKEN_BEGIN_IDX = 151386`
- `IGNORE_INDEX = -100`
- `STOP_INDEX = 2`
- `NUM_TOKENS = 64`

## HF-style package support

The native checkout may provide HF-compatible config/model/processor code. This
skill only documents the expected layout and does not implement or invoke
AutoClasses or conversion utilities. When a checkpoint is meant to be loaded
through AutoClasses, expect matching config, processor, tokenizer, and
remote-code assets in the external checkpoint directory or published bundle.
