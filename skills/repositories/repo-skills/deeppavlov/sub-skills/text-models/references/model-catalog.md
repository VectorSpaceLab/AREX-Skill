# Text-model catalog

Use this page to choose the right DeepPavlov family before editing configs or running a model. For the current live inventory, run `../scripts/list_config_categories.py` from this sub-skill.

## 1) Classification and scalar scoring

Use when the output is a label, label id, probability vector, or a single score.

Representative configs:

- `classifiers/insults_kaggle_bert.json`
- `classifiers/rusentiment_bert.json`
- `classifiers/paraphraser_rubert.json`
- `classifiers/glue/*.json`
- `classifiers/superglue/*.json`
- `classifiers/few_shot_roberta.json`
- `classifiers/query_pr.json`
- `regressors/translation_ranker.json`

Typical signatures:

- One-text classifiers: `x -> y_pred_labels` or `predictions`
- Text-pair classifiers: `sentence1/sentence2`, `question/passage`, `text_a/text_b`, `hypothesis/premise`
- Choice/record tasks: `contexts_list/choices_list`, `idx/query/passage/entities/num_examples`
- Few-shot: `texts, dataset -> y_pred`
- Regression: `source, hypothesis -> pred_score`

Operational notes:

- GLUE, SuperGLUE, few-shot, and regression configs usually rely on HuggingFace datasets and the transformer stack.
- `query_pr` is a classifier config even though its data source is query-prediction data; do not confuse it with document retrieval.
- If the task is about document ranking or open-domain retrieval, reroute to `../retrieval-qa/SKILL.md`.

## 2) Sequence tagging and segmentation

Use when the model must assign tags to tokens or restore sentence boundaries.

Representative configs:

- `ner/ner_bert_base.json`
- `ner/ner_ontonotes_bert.json`
- `ner/ner_rus_bert.json`
- `ner/ner_rus_bert_probas.json`
- `sentence_segmentation/sentseg_dailydialog_bert.json`

Typical signatures:

- NER: `x -> x_tokens, y_pred`
- NER with probabilities: `x -> x_tokens, tokens_offsets, y_pred, probas`
- Sentence segmentation: `x -> x_tokens, punctuated_sents`

Operational notes:

- NER outputs BIO tags over tokens.
- The `_probas` variant is the one to use when you need token offsets and probabilities, not just tags.
- Sentence segmentation expects token sequences; do not send a raw paragraph if the config was built for token lists.

## 3) Entity detection, linking, and relation extraction

Use when the task is span extraction, entity normalization, or relation classification over tagged entities.

Representative configs:

- `entity_extraction/entity_detection_en.json`
- `entity_extraction/entity_detection_ru.json`
- `entity_extraction/entity_extraction_en.json`
- `entity_extraction/entity_extraction_ru.json`
- `entity_extraction/entity_linking_en.json`
- `entity_extraction/entity_linking_ru.json`
- `relation_extraction/re_docred.json`
- `relation_extraction/re_rured.json`

Typical signatures:

- Entity detection: `x -> entity_substr, entity_offsets, entity_positions, tags, sentences_offsets, sentences, probas`
- Entity extraction: `x -> entity_substr, tags, entity_offsets, entity_ids, entity_conf, entity_pages, entity_labels`
- Relation extraction: `tokens, entity_pos, entity_tags -> wikidata_relation_id, relation_name`

Operational notes:

- Entity extraction is two-stage: detection first, then linking.
- Linking configs depend on database/ranker assets and spaCy small model wheels.
- Relation extraction uses token lists plus entity-span metadata; keep entity spans grouped per sample.

## 4) Spelling correction

Use when the model repairs typos or orthographic errors.

Representative configs:

- `spelling_correction/brillmoore_wikitypos_en.json`
- `spelling_correction/levenshtein_corrector_ru.json`

Typical signatures:

- `x -> y_predicted`

Operational notes:

- These pipelines combine tokenization, candidate generation, and language-model selection.
- They are download-heavy: English and Russian spell-correction resources can be several GB.
- Expect optional dependencies around tokenizer, dictionary, and language-model helpers.

## 5) Morpho-syntax parsing

Use when the task is morphological tagging, dependency parsing, or a combined Russian parser.

Representative configs:

- `morpho_syntax_parser/morpho_ru_syntagrus_bert.json`
- `morpho_syntax_parser/syntax_ru_syntagrus_bert.json`
- `morpho_syntax_parser/ru_syntagrus_joint_parsing.json`

Typical signatures:

- Morphological tagging / syntax configs: `x -> y_prettified`
- Joint wrapper: `x_words -> y_parsed`

Operational notes:

- `ru_syntagrus_joint_parsing.json` wraps the morpho and syntax subconfigs.
- The joint parser expects tokenized words in `x_words`, not the raw-text `x` field.
- Dependency parsing uses the `chu_liu_edmonds_transformer` helper.

## 6) Multitask text models

Use when one backbone serves several heads with different task types.

Representative configs:

- `multitask/multitask_example.json`
- `multitask/mt_glue.json`

Typical signatures:

- Multi-input, multi-output configs with exact `chainer.in` / `chainer.out` ordering.
- Heads can cover classification, regression, multiple choice, and NER.

Operational notes:

- Task order matters.
- Mixed-head configs often need custom metrics or a `proba2labels` step.
- Use the multitask docs when you need nested readers or iterator composition.

## 7) Embedding extraction

Use when you need token, subtoken, or sentence vectors rather than a discrete label.

Representative configs:

- `embedder/bert_embedder.json`
- `embedder/bert_sentence_embedder.json`

Typical signatures:

- Full embedder: `texts -> tokens, word_emb, subword_tokens, subword_emb, max_emb, mean_emb, pooler_output`
- Sentence embedder: `texts -> max_emb, mean_emb, pooler_output`

Operational notes:

- The BERT embedder exposes token, subtoken, and sentence-level vectors.
- To swap checkpoints, change the BERT path, vocab, and config fields together.
- The pretrained-vectors documentation also covers 300-dimensional fastText word vectors for standalone embedding use.

## 8) Shared dependency map

Common dependency patterns from the installed package:

- `pytorch.txt` + `transformers.txt`: BERT-backed classifiers, taggers, relation extraction, multitask models, and embedders
- `datasets.txt`: HuggingFace dataset readers and iterators used by GLUE, SuperGLUE, multitask, and some regression configs
- `torchcrf.txt`, `sentencepiece.txt`, `protobuf.txt`: several NER and syntax configs
- `hdt.txt`, `rapidfuzz.txt`, `en_core_web_sm.txt`, `ru_core_news_sm.txt`: entity linking
- `kenlm.txt`, `lxml.txt`, `sortedcontainers.txt`, `sacremoses.txt`: spelling correction

If a config fails before model execution, check the reference above before assuming the model itself is broken.
