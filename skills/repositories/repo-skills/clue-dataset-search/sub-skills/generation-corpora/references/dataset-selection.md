# Generation, Translation, Corpora, and KG Dataset Selection

## When to use this reference

Use this when the user asks for summarization, headline/title generation,
keyphrase generation, machine translation, parallel corpora, pretraining text,
large Chinese corpora, knowledge graph/social graph resources, or general NLP
corpus discovery.

## Summarization resources

Representative rows include LCSTS, Chinese short-text summarization, education
abstractive corpus, NLPCC2017, Byte Cup, NEWSROOM, CNN/DailyMail, Gigaword,
WikiHow, Multi-News, BIGPATENT, legal reports, timeline, PTS, and scientific
summarization corpora. Compare single-document vs multi-document, language,
domain, scale, and license.

## Machine translation resources

Representative rows include WMT2017/2018/2019, UM-Corpus, AI Challenger
translation, MultiUN, NIST OpenMT, MTTT, ASPEC Chinese-Japanese, CWMT/CASIA
series, datum/neu corpora, and translation2019zh. Verify direction, parallel
alignment, license, and whether the link is a direct download, competition page,
or paid catalogue.

## General corpora and knowledge graph resources

Representative rows include NLPIR Weibo/news/short-text resources, Chinese
Wikipedia dumps, Chinese poetry, insurance QA corpus, character decomposition,
brightmart `nlp_chinese_corpus` rows such as news, baike2018qa, webtext2019zh,
wiki2019zh, and the NLPIR Weibo relationship corpus under knowledge graph.

## Selection workflow

1. Determine whether the user needs supervised generation pairs, parallel
   translation, unsupervised pretraining text, QA-style corpus, or graph edges.
2. Search by task plus domain/language (`summarization`, `translation`,
   `wiki`, `weibo`, `parallel`, `knowledge graph`).
3. Check scale and access caveats before suggesting download.
4. Route labeled sentiment/classification needs to `classification-sentiment`
   when the labels are central.
5. Route answer extraction or QA model datasets to `qa-reading` unless the row
   is being used only as broad corpus text.

## Useful helper commands

```bash
python ../../scripts/search_dataset_index.py --category summarization --query LCSTS
python ../../scripts/search_dataset_index.py --category machine-translation --query WMT2019
python ../../scripts/search_dataset_index.py --category corpus --query wiki2019zh
python ../../scripts/search_dataset_index.py --query NLPIR --limit 0
```

## Validation checklist

- State whether the row is paired generation data, parallel translation, broad
  corpus, or graph/social relation data.
- Mention very large downloads, paid/licensed corpora, or privacy-sensitive
  social data.
- Do not claim that pretraining corpora include labels unless the row says so.
- Preserve language direction for translation tasks.
