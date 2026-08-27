# API reference

## CWS and POS conversion
- `jio.cws.word2tag(word_list) -> [chars, tags]`
- `jio.cws.tag2word(chars, tags, verbose=False) -> list[str]`
- `jio.pos.pos2tag(pos_list) -> [chars, tags]`
- `jio.pos.tag2pos(chars, tags, verbose=False) -> list[list[str]]`

## NER conversion
- `jio.ner.entity2tag(token_list, entities) -> list[str]`
- `jio.ner.tag2entity(token_list, tags, verbose=False) -> list[dict]`
- `jio.ner.char2word(char_entity_list, word_token_list, verbose=False) -> list[dict]`
- `jio.ner.word2char(word_entity_list, word_token_list) -> list[dict]`

## Lexicon NER and helpers
- `jio.ner.LexiconNER(entity_dicts)`
- `jio.ner.check_person_name(text) -> bool`
- `f1(gold_lists, pred_lists)` helpers are available in both `jio.cws.f1` and `jio.ner.f1`

## Dataset and batching helpers
- `jio.ner.TokenSplitSentence(func, criterion='fine', max_sen_len=100, combine_sentences=False)`
- `jio.ner.TokenBreakLongSentence(func, max_sen_len=50, overlap=20)`
- `jio.ner.TokenBatchBucket(func, max_sen_len=100, batch_size=1000)`
- `jio.ner.analyse_dataset(dataset_x, dataset_y, ratio=[0.8, 0.05, 0.15], shuffle=True)` for NER
- `jio.text_classification.analyse_dataset(dataset_x, dataset_y, ratio=[0.8, 0.05, 0.15], shuffle=True, multi_label=False)` for text classification
- `jio.ner.collect_dataset_entities(dataset_y)`

## Notes
- `word2tag` / `tag2word` use BI tags.
- `entity2tag` / `tag2entity` use BIOES tags.
- `TokenSplitSentence`, `TokenBreakLongSentence`, and `TokenBatchBucket` are wrappers around an external model function; they do not predict tags by themselves.
- `analyse_dataset` returns train, valid, test, and stats objects; the split can be tiny or empty on very small corpora.
