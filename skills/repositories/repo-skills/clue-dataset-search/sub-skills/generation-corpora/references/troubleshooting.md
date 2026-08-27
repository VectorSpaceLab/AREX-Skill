# Generation and Corpora Troubleshooting

## User asks for pretraining data but query returns summarization rows

Clarify whether they need raw text, title/summary pairs, question-answer text,
or translation pairs. Use corpus rows for raw/pretraining text and summarization
rows for supervised generation.

## Translation direction is unclear

The catalogue often says Chinese-English or multilingual but does not normalize
direction fields. Verify upstream metadata before building a tokenizer or split.

## Very large or paid corpora

LDC, WMT/NIST, Wikipedia, MultiUN, news, and web corpora can be large or
permissioned. Do not download them in an agent session without explicit scope,
storage, and license approval.

## Social-media or user-generated corpora

Weibo and community QA corpora may include privacy-sensitive user content even
when publicly listed. Recommend data-governance review before redistribution or
model release.

## Knowledge graph row looks sparse

The knowledge graph category has a single NLPIR relationship-corpus row in the
captured repository. If the user needs a broader KG benchmark catalogue, use it
as a seed and request authorization for external research.
