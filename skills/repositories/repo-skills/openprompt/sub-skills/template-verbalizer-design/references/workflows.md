# Template/verbalizer workflows

These workflows are for designing and validating prompt components. They intentionally stop before expensive training unless the user has separately selected a training workflow.

## 1. Load a bundled manual classification prompt

Use the bundled corpus when you need repo-maintained templates/verbalizers without the original checkout.

```python
from pathlib import Path
from openprompt.prompts import ManualTemplate, ManualVerbalizer

asset_root = Path("references/prompt-assets/scripts")
classes = ["World", "Sports", "Business", "Tech"]

template = ManualTemplate(tokenizer=tokenizer).from_file(
    asset_root / "TextClassification/agnews/manual_template.txt", choice=0
)
verbalizer = ManualVerbalizer(tokenizer=tokenizer, classes=classes).from_file(
    asset_root / "TextClassification/agnews/manual_verbalizer.txt", choice=0
)
```

Before constructing a model, run:

```bash
python scripts/validate_prompt_assets.py \
  --assets-dir references/prompt-assets/scripts
```

If a target tokenizer is already cached and the user permits using it:

```bash
python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts \
  --tokenizer roberta-large
```

By default tokenizer loading is local-files-only; add `--allow-remote-tokenizer` only with explicit download approval.

## 2. Write a custom hard template safely

```python
from openprompt.data_utils import InputExample
from openprompt.prompts import ManualTemplate

text = '{"placeholder": "text_a"} Overall, it was {"mask"}.'
template = ManualTemplate(tokenizer=tokenizer, text=text)
wrapped = template.wrap_one_example(InputExample(text_a="The movie dragged.", label=0))
```

Checklist:

- Include at least one `{"mask"}` for classification.
- Use `{"placeholder": "text_a"}`/`text_b` for normal fields.
- Use `{"meta": "field"}` only when every `InputExample` has that key in `.meta`.
- Use `{"text": "..."}` when literal text contains punctuation or spaces you want to keep as a single template piece.
- Add `shortenable=False` to labels, titles, or entity mentions that must survive truncation.

## 3. Mix hard and soft tokens

`MixedTemplate` requires the PLM model because it initializes soft-token embeddings from the model input embedding table.

```python
from openprompt.prompts import MixedTemplate

mixed = MixedTemplate(
    model=plm,
    tokenizer=tokenizer,
    text='{"placeholder":"text_a"} {"soft":"Question:"} {"placeholder":"text_b"}? {"mask"}.'
)
```

Soft-token grammar patterns:

- `{"soft"}` or `{"soft": None}`: one randomly initialized soft token.
- `{"soft": "word"}`: soft token initialized from tokenizer pieces for `word`.
- `{"soft": None, "duplicate": 10}`: ten distinct soft tokens.
- `{"soft": None, "duplicate": 10, "same": True}`: ten repeated positions sharing one soft id.
- `{"soft": "the", "soft_id": 1}` and later `{"soft_id": 1}`: reuse the same soft-token id(s).

Use `PtuningTemplate(..., prompt_encoder_type='lstm'|'mlp')` for P-tuning. Use `PTRTemplate` when relation-classification prompts require several mask positions.

## 4. Use soft template or soft verbalizer components

`SoftTemplate` prepends `num_tokens` learned embeddings to an otherwise normal hard template:

```python
from openprompt.prompts import SoftTemplate

soft_template = SoftTemplate(
    model=plm,
    tokenizer=tokenizer,
    num_tokens=20,
    initialize_from_vocab=True,
).from_file(asset_root / "SuperGLUE/RTE/soft_template.txt", choice=0)
```

`SoftVerbalizer` replaces/copies the PLM head and exposes optimizer groups:

```python
from openprompt.prompts import SoftVerbalizer

soft_verbalizer = SoftVerbalizer(tokenizer=tokenizer, model=plm, num_classes=4)
optimizer_groups = [
    {"params": soft_verbalizer.group_parameters_1, "lr": 3e-5},
    {"params": soft_verbalizer.group_parameters_2, "lr": 3e-4},
]
```

Do not use these components in a no-model static context; they require model embedding/head inspection.

## 5. Multi-mask PTR relation prompt

The repo PTR assets use five masks and a JSON/JSONL verbalizer mapping each class to five label words.

```python
from openprompt.prompts import PTRTemplate, PTRVerbalizer

template = PTRTemplate(model=plm, tokenizer=tokenizer).from_file(
    asset_root / "RelationClassification/TACRED/ptr_template.txt"
)
verbalizer = PTRVerbalizer(tokenizer=tokenizer, classes=relation_labels).from_file(
    asset_root / "RelationClassification/TACRED/ptr_verbalizer.jsonl"
)
```

PTR invariants:

- each class must provide the same number of label words as there are masks;
- each mask gets its own `One2oneVerbalizer` internally;
- repeated words such as `person` or `was` across relation classes are expected because final labels are combined by mask-wise logic.

## 6. Generation verbalizer for dynamic target text

Use `GenerationVerbalizer` when a class maps to generated target text, not a fixed classification projection.

```python
from openprompt.prompts import GenerationVerbalizer

verbalizer = GenerationVerbalizer(tokenizer=tokenizer, classes=class_labels, is_rule=True).from_file(
    asset_root / "SuperGLUE/COPA/generation_verbalizer.txt"
)
```

When `is_rule=True`, each label word can be a template fragment such as `{"meta":"choice1"}`. These fragments fill `InputExample.tgt_text`; they are not classification label words and may be multi-token target strings.

## 7. LM-BFF template and verbalizer generation

LM-BFF search is expensive and needs model/data/cache approval. Use it only when static assets or manual design are insufficient.

Template search pattern from `tutorial/3.1_LMBFF.py`:

1. Build an initial `ManualVerbalizer`.
2. Use `LMBFFTemplateGenerationTemplate` with a template containing `{"meta":"labelword"}` and generation masks.
3. Accumulate a full few-shot batch in `T5TemplateGenerator`.
4. Generate candidate parsed templates.
5. Score each candidate with a validation loop.
6. Use a no-parse manual-template wrapper when the generator returns a list of parsed dict pieces.

Label-word search pattern:

1. Build `RobertaVerbalizerGenerator(model=plm, tokenizer=tokenizer, candidate_num=..., label_word_num_per_class=...)`.
2. Register masked-LM probabilities from the training dataloader.
3. Generate candidate label-word groups.
4. Validate candidates against held-out data before selecting.

Static skill guidance: document the desired generation parameters and constraints first; do not start LM-BFF generation until the user has approved model downloads, GPU/CPU runtime, dataset access, and evaluation budget.

## 8. Calibration workflow

Calibration estimates prior logits from a support/context dataloader and registers them on the verbalizer.

```python
from openprompt.utils.calibrate import calibrate

cc_logits = calibrate(prompt_model, support_dataloader)
prompt_model.verbalizer.register_calibrate_logits(cc_logits)
```

Operational notes:

- A support dataloader can contain real support examples with labels removed or a template-only pseudo example such as `InputExample(text_a="", text_b="")`.
- The source tutorials use calibration with `ManualVerbalizer` and `KnowledgeableVerbalizer`.
- For `KnowledgeableVerbalizer`, registration can remove low-prior label-word candidates according to `candidate_frac`.
- Shape mismatches usually mean the template mask count, verbalizer type, or class/label-word shape is inconsistent.

## 9. Asset editing workflow

When adapting assets for a user task:

1. Copy the nearest bundled asset into the user's working artifact area or a new runtime reference path.
2. Keep template files one template per non-empty line.
3. Keep manual `.txt` verbalizers as one class per non-empty line, comma-separated words per class, blank lines between alternative verbalizers.
4. Keep `.json`/`.jsonl` verbalizers as full JSON documents, because OpenPrompt's `from_file` calls `json.load` even for `.jsonl`.
5. Run the validator on the edited directory.
6. If using a target tokenizer, rerun with `--tokenizer` to catch true tokenizer-level multi-token label words.
