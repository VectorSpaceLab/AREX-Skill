# Bundled OpenPrompt prompt assets

This sub-skill bundles the repository-maintained prompt asset corpus so a future agent can inspect, copy, validate, and adapt OpenPrompt template/verbalizer assets without the original OpenPrompt checkout.

## Location

Runtime asset root, relative to this sub-skill:

```text
references/prompt-assets/scripts/
```

The subtree preserves the source `scripts/` layout and contains 78 `.txt`, `.json`, and `.jsonl` assets. `references/prompt-assets/MANIFEST.json` records relative paths, byte sizes, and SHA-256 hashes. `references/prompt-assets/ADAPTATIONS.md` records small format repairs made during bundling.

## Source and adaptation policy

Source repository snapshot: OpenPrompt commit `f6fb080ef755c37c01b7959e7560d007049510e8`.

Bundling rule: copy the source `scripts/**/*.txt`, `scripts/**/*.json`, and `scripts/**/*.jsonl` prompt assets, then make only minimal repairs needed for OpenPrompt runtime file contracts and static validation. See `prompt-assets/ADAPTATIONS.md` for the exact changed files.

Important adaptations:

- FewGLUE manual verbalizers originally used one whitespace-separated line such as `Yes No`; bundled copies use one class line per label.
- SuperGLUE WSC's empty manual verbalizer is filled with a minimal `Yes`/`No` file, while the original generation verbalizer remains available and is preferred for WSC generation-style workflows.
- Two obvious whitespace multi-word entries were removed from Amazon/IMDB knowledgeable verbalizers so strict static label-word checks are actionable.
- Generation verbalizer files are left as rule-like template snippets; multi-token target text there is intentional.

## Corpus map

| Subtree | Asset types | Typical use |
|---|---|---|
| `TextClassification/agnews` | manual, mixed, soft, P-tuning templates; manual, knowledgeable, multiword verbalizers | News topic classification prompt examples. |
| `TextClassification/amazon`, `imdb`, `dbpedia`, `yahoo_answers_topics`, `mnli` | manual templates/verbalizers and knowledgeable/multiword variants | Text-classification label-word examples with small and large class sets. |
| `SuperGLUE/*` | soft templates, manual verbalizers, generation verbalizers | Boolean, entailment, COPA, WSC, MultiRC, RECORD generation/manual prompt assets. |
| `FewGLUE/*` | manual, soft-manual, P-tuning templates; manual verbalizers | FewGLUE-oriented prompt assets. |
| `RelationClassification/{TACRED,TACREV,ReTACRED}` | PTR template and PTR verbalizer JSON/JSONL | Multi-mask relation extraction prompts. |
| `RelationClassification/SemEval/temp.txt` | tabular relation mapping asset | Static reference for SemEval relation-label wording. |
| `Typing/FewNERD` | manual/mixed templates and manual/knowledgeable verbalizer JSON | Entity typing label-word examples. |
| `LMBFF/{SST-2,SNLI}` | manual templates, auto-template seed templates, initial/manual verbalizers | LM-BFF template/verbalizer generation seeds. |
| `CondGen/webnlg_2017` | manual generation template | Conditional generation example. |
| `CoT/csqa.txt` | few-shot chain-of-thought text prompt | Text reference, not OpenPrompt template grammar. |
| `UltraChat/template.txt` | template with `meta` and `post_processing` lambda | Dialogue/generation prompt asset. |

## File format contracts

### Template `.txt`

- One template candidate per non-empty line.
- Loaded by `Template.from_file(path, choice=i)`.
- Must parse as OpenPrompt dict/set grammar and normally include `{"mask"}`.
- Multiple masks are expected for PTR templates and LM-BFF `template_for_auto_t.txt` seed templates.

Example:

```text
{"placeholder": "text_a"} {"placeholder": "text_b"} This topic is about {"mask"} .
```

### Manual/knowledgeable verbalizer `.txt`

- One class per non-empty line.
- Commas separate multiple label words for the same class.
- Blank lines separate alternative verbalizer groups for `choice`.
- Whitespace does **not** separate classes.

Example:

```text
bad,terrible
excellent,great
```

### Verbalizer `.json` / `.jsonl`

OpenPrompt source calls `json.load` for both extensions, so full JSON documents are safest. Supported shapes include:

```json
{"negative": ["bad", "terrible"], "positive": ["good", "great"]}
```

or a list of alternative verbalizers:

```json
[
  {"negative": ["bad"], "positive": ["good"]},
  {"negative": ["terrible"], "positive": ["great"]}
]
```

PTR verbalizers use a dict from relation class to one label word per mask:

```json
{"per:title": ["person", "'s", "title", "is", "title"]}
```

### Generation verbalizer `.txt`

Generation verbalizers may contain literal target text or rule-like template snippets such as:

```text
{"meta":"choice1"}
{"meta":"choice2"}
```

These are target-text rules for `GenerationVerbalizer(is_rule=True)`, not fixed single-token class label words.

## Validation

Default static validation:

```bash
python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts
```

Expected clean bundled-corpus signal at draft time: 78 asset files, 76 template lines, 38 verbalizer files, 10 JSON/JSONL files, 0 errors. Duplicate warnings may appear for knowledgeable, PTR, and broad entity-typing assets because those workflows deliberately reuse scaffold or candidate words.

Useful stricter modes:

```bash
# Treat ordinary duplicate label words as publication-blocking issues.
python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts --strict-duplicates

# Check exact tokenizer splitting when the tokenizer is locally available.
python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts --tokenizer roberta-large
```

The tokenizer mode is local-files-only by default. Add `--allow-remote-tokenizer` only after user approval for network/model-cache effects.

## How to adapt assets for a user task

1. Copy the closest asset into the user's task directory or a new skill reference path.
2. Update class names/order from the processor or dataset contract.
3. Keep the original bundled file intact unless maintaining a revised skill corpus.
4. Validate the edited directory before use.
5. If using RoBERTa/T5/BERT-specific label words, run tokenizer validation with the exact target tokenizer.
6. Record any class-order or label-word changes in the task report.
