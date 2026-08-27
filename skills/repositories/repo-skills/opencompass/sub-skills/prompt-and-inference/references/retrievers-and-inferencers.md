# Retrievers and Inferencers

OpenCompass prompt construction is a three-part pipeline:

1. The dataset reader exposes train/test splits plus `input_columns` and `output_column`.
2. A retriever returns train/index examples to use as in-context examples for each test sample.
3. An inferencer asks the retriever to render either generation prompts or label-candidate prompts.

## Retriever Selection

| Retriever | Use When | Key Requirements |
| --- | --- | --- |
| `ZeroRetriever` | 0-shot evaluation | Does not need train examples; returns `[]` for every test item. |
| `FixKRetriever` | Reproducible few-shot examples | `fix_id_list` indices must exist in the train/index split. |
| `RandomRetriever` | Quick random few-shot experiments | Needs a non-empty train/index split and `ice_num <= len(train)`. |
| `BM25Retriever` / `TopkRetriever` family | Similarity-based few-shot retrieval | Usually needs tokenization/embedding dependencies and train/index text. |
| `MDLRetriever` / `DPPRetriever` / `VotekRetriever` | Advanced selection strategies | More expensive; verify dependencies and candidate/label assumptions. |

`ZeroRetriever` is the safest default while debugging templates because it avoids train-split and dependency issues.

## In-Context Example Flow

For a test sample, the retriever:

- calls `retrieve()` to produce a list of train indices;
- builds `ice` with `generate_ice(indices, ice_template)`;
- inserts `ice` through `ice_token` when rendering the test prompt;
- uses the dataset reader `output_column` as the label/answer field for ICE examples.

If `ice_template` is missing while the retriever returns non-empty indices, OpenCompass raises an assertion asking you to either specify `ice_template` or use `ZeroRetriever`.

## GenInferencer

Use `GenInferencer` when the model must produce free text or a normalized answer string.

Minimal pattern:

```python
infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template='Q: {question}\nA: {answer}',
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer, max_out_len=64),
)
```

Generation-specific behavior:

- `GenInferencer` calls `generate_prompt_for_generate_task`.
- The test sample `reader_cfg.output_column` is replaced with `gen_field_replace_token` before formatting.
- `gen_field_replace_token=''` produces blank answer slots such as `A: `.
- The gold answer is still stored separately from the prompt when `output_column` exists.
- `generation_kwargs` belong on the inferencer when a backend supports generation options.

Do not debug a blank answer slot as a missing template field until you confirm whether the blank field is the configured output column.

## PPLInferencer

Use `PPLInferencer` when the answer is selected from candidate labels by comparing per-label prompt likelihood/perplexity.

Minimal pattern:

```python
infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template=dict(
            A='Q: {question}\nA. {A}\nB. {B}\nAnswer: A',
            B='Q: {question}\nA. {A}\nB. {B}\nAnswer: B',
        ),
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=PPLInferencer),
)
```

PPL-specific behavior:

- `PPLInferencer` asks the retriever for labels.
- Labels come first from `prompt_template.template.keys()` if that template is a dictionary.
- If not, labels can come from a keyed `ice_template` with `ice_token`.
- If no keyed template is available, labels fall back to unique values from `reader_cfg.output_column` in the test split.
- The chosen prediction is the label with the lowest PPL score.
- `normalizing_str` requires string prompts and uses `sep_token` to separate context from answer.

Use explicit candidate templates for multiple-choice tasks; relying on unique output-column values can be accidental and brittle.

## Reader Config and Column Masking

Prompt behavior depends on `reader_cfg`:

```python
reader_cfg = dict(
    input_columns=['question'],
    output_column='answer',
)
```

Effects:

- `input_columns` determine the source fields for default reader operations and some chat inference helpers.
- `output_column` identifies the gold answer field.
- In generation prompts, the `output_column` field is overwritten by `gen_field_replace_token` before template substitution.
- In ICE examples, the train example output column is available so few-shot answers appear.
- In PPL tasks, the output column can provide labels/golds but candidate templates should still be explicit.

To prevent answer leakage, keep the answer field in `output_column` and avoid duplicating it under another template field name such as `{target_text}` unless the dataset preprocessor masks that alias too.

## Debugging with Prompt Preview

Use the bundled preview script before running real inference:

```bash
python scripts/render_prompt_preview.py --mode gen
python scripts/render_prompt_preview.py --mode ppl --label B
python scripts/render_prompt_preview.py --dialogue --show-raw
```

The script uses tiny embedded samples and mimics the core masking, ICE insertion, missing-field preservation, and dialogue structure. It does not download datasets or instantiate models.

## When to Escalate to Other Sub-skills

- Dataset class loading, split definitions, or `reader_cfg` construction: `configuration-and-datasets`.
- Tokenizer truncation, model-side chat parser behavior, API message serialization, or backend flags: `model-backends`.
- Summarizer/evaluator mismatch after predictions are produced: the evaluation/summarization sub-skill.
