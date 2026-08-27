# Classification and Sentiment Dataset Selection

## When to use this reference

Use this when the user asks for supervised text classification, topic/news/app
classification, sentiment polarity, emotion recognition, aspect-based sentiment,
entity sentiment, or opinion mining resources.

## Classification rows

Representative `text-classification` candidates include:

- Daguan Cup long-text classification;
- Toutiao news title/text classification;
- THUCNews and Fudan news classification;
- IFLYTEK long-text app classification;
- Sogou news resources;
- ChineseNlpCorpus-derived rows such as ChnSentiCorp, waimai_10k,
  online_shopping_10_cats, weibo_senti_100k, dmsc_v2, and e-commerce reviews.

Some rows under text classification are broad corpora rather than clean
classification benchmarks. Verify label columns and split files at the upstream
source before promising supervised training readiness.

## Sentiment/emotion rows

Representative `sentiment-analysis` candidates include:

- NLPCC 2013/2014 emotion and sentiment tasks;
- Weibo Emotion Corpus and weibo_senti_100k;
- BDCI automotive aspect/topic sentiment;
- AI Challenger fine-grained review sentiment;
- finance negative-entity judgment;
- e-commerce opinion extraction and Sohu entity sentiment.

## Selection workflow

1. Determine whether the user needs document/topic classification, binary or
   multiclass sentiment, emotion labels, aspect sentiment, entity sentiment, or
   opinion extraction.
2. Search both `text-classification` and `sentiment-analysis` when the request
   mentions comments, reviews, Weibo, polarity, or emotion.
3. Compare label schema hints: class count, polarity values (`0/1/-1`), aspect
   attributes, entity lists, or topic labels.
4. Warn when rows list corpus scale but omit train/dev/test split or license.

## Useful helper commands

```bash
python ../../scripts/search_dataset_index.py --category text-classification --query IFLYTEK
python ../../scripts/search_dataset_index.py --category sentiment-analysis --query emotion
python ../../scripts/search_dataset_index.py --query aspect --language Chinese
python ../../scripts/search_dataset_index.py --query ChineseNlpCorpus --limit 0
```

## Validation checklist

- State whether the recommendation is classification, sentiment, aspect
  sentiment, or corpus-only.
- Include label/schema hints only when the catalogue row mentions them.
- Warn that ChineseNlpCorpus/GitHub rows may need upstream format inspection.
- Do not route semantic equivalence or NLI tasks here; use `matching-nli`.
