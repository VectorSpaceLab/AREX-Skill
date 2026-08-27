# Data formats

## NER entity format
A single sample is usually represented as:

```text
[
  "胡静静在水利局工作。",
  [
    {"text": "胡静静", "offset": [0, 3], "type": "Person"},
    {"text": "水利局", "offset": [4, 7], "type": "Organization"}
  ]
]
```

## CWS format
- Input words: `['他', '指出', '：', '近', '几', '年', '来', '，', '足球场', '风气', '差劲', '。']`
- `word2tag` returns `[chars, tags]` where `tags` is BI labels.

## POS format
- Input POS pairs: `[['他', 'r'], ['指出', 'v'], ['：', 'w'], ['近', 'a']]`
- `pos2tag` returns `[chars, tags]` where `tags` uses `B-<pos>` / `I-<pos>`.

## NER tag format
- `entity2tag` / `tag2entity` use BIOES.
- A valid entity span must match the token offsets exactly.

## Dataset split helpers
- `analyse_dataset` expects parallel `dataset_x` and `dataset_y` lists.
- For text classification, `multi_label=True` means each label item is a list of labels.
- The returned `stats` object summarizes counts and class proportions for each split.
