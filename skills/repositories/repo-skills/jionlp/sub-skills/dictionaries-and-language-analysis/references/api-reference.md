# API reference

## Language-analysis helpers
- `jio.keyphrase.extract_keyphrase(text, top_k=5, with_weight=False, func_word_num=1, stop_word_num=0, max_phrase_len=25, min_phrase_len=1, topic_theta=0.5, allow_pos_weight=True, strict_pos=True, allow_length_weight=True, allow_topic_weight=True, without_person_name=False, without_location_name=False, remove_phrases_list=None, remove_words_list=None, specified_words={}, bias=None)`
- `jio.summary.extract_summary(text, summary_length=200, lead_3_weight=1.2, topic_theta=0.2, allow_topic_weight=True)`
- `jio.sentiment.LexiconSentiment()`
- `jio.new_word.new_word_discovery(input_file, min_freq=10, min_mutual_information=80, min_entropy=3)`
- `jio.text_classification.analyse_freq_words(dataset_x, dataset_y, min_word_freq=10, min_word_threshold=0.8)`
- `jio.text_classification.analyse_dataset(dataset_x, dataset_y, ratio=[0.8, 0.05, 0.15], shuffle=True, multi_label=False)`
- `jio.bpe.byte_level_bpe.encode(text)` / `decode(chars)`

## MELLM
- `MELLM(llm_names, llm_apis, exam_questions, self_grading=True, stop_criteria=1e-05, max_epoch=20)`
- Public methods: `answer_questions`, `normalize_grading_result`, `norm_test`, `build_grading_matrix`, `run_whole`, `run_singular`

## Notes
- `extract_keyphrase` and `extract_summary` rely on packaged idf/topic resources and `jiojio` segmentation / tagging.
- `analyse_freq_words` expects tokenized text and class labels.
- `new_word_discovery` expects a line-oriented UTF-8 corpus file and often returns an empty dict on tiny fixtures.
- `MELLM` is an evaluation wrapper: it needs callable LLM APIs and a list of exam questions; it does not download model weights.
- `byte_level_bpe` is exposed as `jio.bpe.byte_level_bpe`, not as a root attribute.
