# Hugging Face export

## CLI contract

Publish a trained experiment with:

```bash
python llm_studio/publish_to_hugging_face.py -p <experiment-dir> -d cuda:0
```

Flags used by the runtime exporter:

| Flag | Meaning |
| --- | --- |
| `-p`, `--path_to_experiment` | Experiment output directory to export |
| `-d`, `--device` | Preparation device: `cpu`, `cpu_shard`, or `cuda:<index>` |
| `-a`, `--api_key` | Hugging Face write token |
| `-u`, `--user_id` | Hugging Face account name |
| `-m`, `--model_name` | Repository/model name to create on the Hub |
| `-s`, `--safe_serialization` | Forwarded to the backbone push step |

If `model_name` is omitted, the runtime derives it from the experiment folder
name and normalizes it to a Hub-safe repository name.

## What gets uploaded

The export flow prepares the experiment locally, then uploads the artifacts to a
private Hugging Face model repo:

1. tokenizer files
2. model card generated from the matching template
3. optional `classification_head.pth`
4. optional `regression_head.pth`
5. `cfg.yaml`
6. backbone weights, using the selected safe-serialization setting
7. `hf.yaml` bookkeeping in the experiment output directory

For generation-style experiments, the tokenizer chat template is rebuilt from
the saved prompt, answer, and optional system tokens before upload.

## Authentication and network

Publishing needs a Hugging Face token with write access.

- If `api_key` is supplied, the runtime logs in with that token.
- If `user_id` is omitted, the runtime resolves the logged-in account.
- If no token is supplied, the runtime relies on an already authenticated Hub
  session.

The upload path also honors `HF_HUB_ENABLE_HF_TRANSFER`. Leave it enabled when
transfer acceleration is stable; disable it when proxies, partial network
support, or the helper itself cause problems.

## Device rules

The exporter accepts only these device forms:

- `cpu`
- `cpu_shard`
- `cuda:<index>`

Use `cpu_shard` only when the runtime can shard the model across visible GPUs.
Use a CUDA device only when that GPU is actually present in the session.

## Safe serialization and disk space

The export path checks available local disk space before serializing the model.
That matters because the model is prepared locally before the Hub upload starts.

`safe_serialization` is forwarded to the backbone push step. Keep the default
setting unless the downstream consumer requires a different format.

## Model card and template layout

The model card and the experiment-summary card are template-driven. The runtime
selects a template family from the problem type and fills in the saved config,
architecture summary, library versions, and sample generation settings when the
problem type is generation-style.

Template families bundled with the package:

| Problem type family | Model card template | Summary template |
| --- | --- | --- |
| Causal language modeling | `text_causal_language_modeling_model_card_template.md` | `text_causal_language_modeling_experiment_summary_card_template.md` |
| Causal classification | `text_causal_classification_model_card_template.md` | `text_causal_classification_experiment_summary_card_template.md` |
| Causal regression | `text_causal_regression_model_card_template.md` | `text_causal_regression_experiment_summary_card_template.md` |
| Sequence-to-sequence | `text_sequence_to_sequence_modeling_model_card_template.md` | `text_sequence_to_sequence_modeling_experiment_summary_card_template.md` |

Generation-style cards include a sample chat payload and generation settings.
Non-generation cards keep the card focused on the backbone and saved config
metadata.

## Repo-name normalization

The Hub repo name is normalized to a safe slug by replacing non-alphanumeric
characters, trimming leading or trailing hyphens, and truncating the result to
96 characters.

If a user-provided model name collides with an existing repo or becomes empty
after normalization, pick a clearer name before publishing.

## h2oGPT handoff

A published or downloaded model can be loaded by h2oGPT from either a Hub repo
id or an extracted local folder:

```bash
python generate.py --base_model=<repo-id-or-extracted-folder>
```

If the model was downloaded as a zip file, extract it before handing it to
h2oGPT.