# OpenPrompt Data And Config Workflows

Use these workflows to inspect or prepare OpenPrompt configs without launching training, loading PLMs, or downloading datasets.

## 1. Triage An Experiment YAML

1. Identify the config file and the directory that should anchor relative dataset and asset paths.
2. From the sub-skill root, run the bundled inspector:

```bash
python scripts/inspect_openprompt_config.py \
  --config /path/to/openprompt_config.yaml \
  --base-dir /path/to/project-or-asset-root \
  --check-paths
```

3. Review:
   - `dataset.name` is a known processor name.
   - `dataset.path` is either a real local directory or intentionally blank for a HuggingFace-backed processor.
   - Selected `template`, `verbalizer`, `task`, and `learning_setting` branches are present or supplied by OpenPrompt defaults.
   - Prompt asset `file_path` entries resolve under the chosen base directory.
   - Example-local paths have been replaced with the user's actual data/cache/asset locations.

Do not run `experiments/cli.py` as a training command during triage. In OpenPrompt, the CLI proceeds from config parsing into `load_dataset`, PLM loading, dataloaders, and runner execution.

## 2. Adapt A Classification Config Pattern

Distilled pattern from the repo's manual/mixed/soft/proto classification examples:

```yaml
dataset:
  name: agnews                 # any known local or HuggingFace processor name
  path: <DATA_ROOT>/TextClassification/agnews

plm:
  model_name: bert             # model family used by openprompt.plms
  model_path: bert-large-cased # HF id, cache name, or explicit local model path
  optimize:
    freeze_para: false
    lr: 0.00003

train:
  batch_size: 2
dev:
  batch_size: 8
test:
  batch_size: 8

template: manual_template      # selects the branch of the same name
verbalizer: manual_verbalizer
manual_template:
  choice: 0
  file_path: <ASSET_DIR>/manual_template.txt
manual_verbalizer:
  choice: 0
  file_path: <ASSET_DIR>/manual_verbalizer.txt

learning_setting: few_shot
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
  num_examples_per_label: 10
  also_sample_dev: true
  num_examples_per_label_dev: 10
  seed: [123, 456, 789]
```

Operational notes:

- Use project-local absolute paths or a documented `--base-dir`; do not keep repo-example `scripts/...` or `datasets/...` paths unless those directories exist in the user's project.
- `template` and `verbalizer` are selectors. Their scalar values should equal a branch name such as `manual_template` or `manual_verbalizer`.
- `choice` selects an entry inside prompt asset files; validate that the asset file exists before training.
- `num_gpus`, `cuda_visible_devices`, and `model_parallel` are only flags until the training workflow verifies hardware and torch/CUDA compatibility.

## 3. Adapt A HuggingFace/SuperGLUE Config Pattern

Repo examples for `super_glue.*` processors often leave `dataset.path` blank. That means the HuggingFace `datasets` wrapper will determine dataset source/cache at runtime.

```yaml
dataset:
  name: super_glue.boolq
  path: null

plm:
  model_name: t5
  model_path: t5-large

dataloader:
  max_seq_length: 256
  decoder_max_length: 256

template: soft_template
verbalizer: manual_verbalizer
soft_template:
  parent_config: template
  num_tokens: 20
manual_verbalizer:
  parent_config: verbalizer
  label_words: [["yes"], ["no"]]

learning_setting: full
```

Safety notes:

- Static inspection can validate the selector structure, but actual `datasets.load_dataset` may require network or a populated cache.
- If the user wants offline execution, require a prepared HuggingFace cache or switch to a local processor layout.

## 4. Adapt A Generation Config Pattern

Distilled from the repo WebNLG/generation example:

```yaml
dataset:
  name: webnlg
  path: <DATA_ROOT>/CondGen/webnlg_2017

task: generation
generation:
  parent_config: task
  max_length: 512
  num_beams: 5

plm:
  model_name: gpt2
  model_path: gpt2-medium

learning_setting: full
template: manual_template
verbalizer: null
manual_template:
  parent_config: template
  text: '{"placeholder":"text_a"} {"special":"<eos>"} {"mask"}'
```

Operational notes:

- Generation examples should populate `tgt_text` through their processor.
- `verbalizer` may be empty for generation because `PromptForGeneration` does not use a classification verbalizer.
- `dataloader.decoder_max_length` and `generation.max_length` have different meanings; `generation.max_length` includes generated sequence behavior in the runner.

## 5. Adapt An LM-BFF / Auto Template-Verb Pattern

Repo LM-BFF configs select classification with automatic template/verbalizer flags and generator branches. Keep this as an advanced configuration; actual generator runs are expensive and may require large model caches.

```yaml
task: classification
classification:
  parent_config: task
  auto_t: true
  auto_v: true

template_generator:
  plm:
    model_name: t5
    model_path: t5-large
  max_length: 20
  target_number: 2

verbalizer_generator:
  candidate_num: 1
  label_word_num_per_class: 1
  score_fct: llr
  normalize: true
```

Safe validation checks only that these keys are present and typed plausibly. Runner behavior belongs to the training sub-skill.

## 6. Use Processors Directly For Tiny Fixture Checks

When the user supplies a tiny local fixture and asks for processor behavior, prefer direct processor construction over `load_dataset` so failures are localized and do not exit the process.

Example shape:

```python
from openprompt.data_utils.text_classification_dataset import PROCESSORS
processor = PROCESSORS["sst-2"]()
examples = processor.get_train_examples("/path/to/SST-2-fixture")
print(examples[0].text_a, examples[0].label)
```

Do this only after the user has provided files and approved reading them. For HuggingFace processors, avoid direct calls unless network/cache use has been approved.

## 7. Few-Shot Sampling Workflow

1. Ensure the dataset has `label` fields. Generation-only examples normally cannot use per-label sampling.
2. Decide exactly one train sampling strategy: total examples or examples per label.
3. Decide whether the dev set should also be sampled.
4. Use deterministic seeds when comparing runs.
5. Watch for labels with too few examples; `FewShotSampler` logs a warning and samples what exists.

Config pattern:

```yaml
learning_setting: few_shot
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
  num_examples_per_label: 4
  also_sample_dev: true
  num_examples_per_label_dev: 4
  seed: [13]
```

## 8. Handoff To Training/GPU Workflows

Before handing a validated config to training:

- Confirm dataset and prompt asset paths exist.
- Confirm model IDs/paths and tokenizer family are appropriate for the chosen template/verbalizer.
- Record any HuggingFace dataset/model downloads that will be required.
- Record environment flags (`num_gpus`, `cuda_visible_devices`, `model_parallel`) as requested behavior, not proof of backend readiness.
- Route runner selection, checkpoint/resume/test behavior, and GPU constraints to `../training-and-generation/`.
