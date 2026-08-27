# Evaluation workflows

## 1. Validate and classify the input

An inference artifact is a JSON object with `prompt` (the exact prompt given
to PointLLM) and `results` (an array). Every row has `object_id`,
`ground_truth`, and `model_output`. Objaverse generation writes the annotation
text as `ground_truth`; ModelNet generation writes the integer class index and
also `label_name`. Use the bundled validator before judging. It deliberately
checks only structure and values; it does not load a model, dataset, tokenizer,
or API client.

Choose one of these paths:

| Benchmark | Generation task | Judge `eval_type` | Main interpretation |
|---|---|---|---|
| Objaverse | `classification`, prompt 0/1 | `open-free-form-classification` | GPT decides whether generated and reference descriptions name the same general object/concept |
| Objaverse | `captioning`, prompt 2 | `object-captioning` | GPT scores reference aspects covered by the generated caption from 0 to 100 |
| ModelNet40 | prompt 0/1 | `modelnet-close-set-classification` | GPT maps free-form output to one of 40 class indices |
| Objaverse captions | already generated caption JSON | traditional evaluator | local n-gram, overlap, and embedding proxies |

## 2. Objaverse generation and scoring

The intended benchmark is the small validation annotation set of 200 objects;
the released 3,000-object annotation set is an alternative. Generation names
files using the annotation basename, benchmark, task, and prompt index, then
places them under the model's `evaluation` directory. Keep the exact prompt in
the artifact because prompt index changes the task:

- 0: `What is this?`
- 1: `This is an object of `
- 2: `Caption this 3D model in detail.`

Use classification with index 0 or 1. Use captioning with index 2. The source
prints a warning for mismatched combinations but does not hard-fail, so the
operator must reject an accidental mismatch. With `--start_eval`, generation
can immediately invoke the mapped OpenAI judge; otherwise score the saved JSON
in a separate, auditable step.

## 3. ModelNet40 generation and scoring

ModelNet generation writes `ModelNet_classification_prompt<N>.json`. Each row
uses the dataset index as `object_id`, numeric `ground_truth` in 0..39,
`model_output`, and the corresponding `label_name`. The loader asserts that
shuffle is false: changing order breaks the identity relationship used in the
result. `--subset_nums` is useful for a bounded smoke test; record it because
subset results are not full-benchmark results.

The close-set judge expands its prompt with the 40 category names and expects
`index#class#short reason`. A response outside 0..39, `NA`, or unparsable text
is marked invalid and then assigned a random category using the source's fixed
random seed. The assigned category is retained in `gpt_cls_result`, while
`gpt_cls_label` is `INVALID`. This means headline accuracy includes possible
chance hits from invalid answers; `clean_accuracy` removes those hits.

## 4. Resume-safe OpenAI run

The evaluator derives its final output name from the input basename and model
name, and its temporary name by replacing `.json` with
`_processed_temp.json`. It resumes by loading the temporary object, restoring
counters and per-row results, and dropping already processed rows by
`object_id`. Parallel mode uses unordered worker results, so row order in the
final list is not an input-order guarantee. Successful completion deletes the
temporary file; preserve it after interruption or failure.

Before parallel work, run a one- or few-row structural check and confirm the
credential, selected model, provider entitlement, rate limits, worker count,
and cost ceiling. The source uses historical prices and reports prompt and
completion token totals. `gpt-4` is recommended for open classification and
captioning; ModelNet's README example uses `gpt-3.5-turbo-0613`, but model
choice is an evaluation-design decision that must be recorded.

## 5. Traditional caption workflow

Run only on an Objaverse captioning artifact. The evaluator loads the result
JSON and writes a sibling `_evaluated_traditional.json`. It computes each row's
BLEU-1/2/3/4 with smoothing, ROUGE-1/2/L F scores, METEOR, Sentence-BERT
cosine similarity (`all-mpnet-base-v2`), and SimCSE cosine similarity
(`princeton-nlp/sup-simcse-roberta-large`). It then emits per-row `scores` and
string-formatted averages in `overall_scores`.

This path downloads NLTK WordNet data and both embedding models if absent. It
is not a no-network smoke test. Empty model output is replaced internally by
`##`, and is therefore represented as a zero-like comparison rather than
causing a blank-input crash. Use the semantic embedding scores as rough
proxies only; the project explicitly cautions against relying on BLEU,
ROUGE-L, and METEOR because short captions can score deceptively well.
