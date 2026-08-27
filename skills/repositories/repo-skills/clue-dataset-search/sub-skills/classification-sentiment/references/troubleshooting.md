# Classification and Sentiment Troubleshooting

## Broad corpus mistaken for labeled classification

Rows such as general Chinese corpora or review corpora may not expose a clean
classification split in the catalogue. Ask the user to verify upstream files and
labels before using them as supervised data.

## Aspect sentiment vs plain polarity

Aspect datasets include attributes, opinion terms, polarity, and sometimes
attribute categories. Do not reduce them to binary positive/negative sentiment
unless the user explicitly wants a simplified task.

## Duplicate weibo_senti_100k or ChineseNlpCorpus rows

The same upstream collection can appear through classification and sentiment
routes. Preserve the user's intended label task and cite the category row used.

## License field missing for competition data

Competition-hosted classification/sentiment resources may require account
registration or non-redistribution terms. Treat blank license as unknown.
