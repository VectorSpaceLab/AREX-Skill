# API reference

## Back translation
- `BackTranslation(mt_apis=[])`
- API wrappers: `BaiduApi(appkey_obj_list=None, gap_time=0, url=..., lang_pool=[...])`, `YoudaoFreeApi(...)`, `YoudaoApi(...)`, `GoogleApi(...)`, `TencentApi(...)`, `XunfeiApi(...)`

Behavior:
- `BackTranslation.__call__(text)` runs each configured translation API in parallel.
- Each API must be callable with `text`, `from_lang`, and `to_lang`.
- The wrapper filters duplicate or overly short/long outputs before returning the augmentation list.

## Local augmenters
- `SwapCharPosition(text, augmentation_num=3, swap_ratio=0.02, seed=1, scale=1.0) -> list[str]`
- `HomophoneSubstitution(text, augmentation_num=3, homo_ratio=0.02, allow_mispronounce=True, seed=1) -> list[str]`
- `RandomAddDelete(text, augmentation_num=3, seed=1, add_ratio=0.02, delete_ratio=0.02) -> list[str]`
- `ReplaceEntity(entities_dict)`
  - call form: `replace_entity(text, entities, augmentation_num=3, replace_ratio=0.1, seed=1) -> (texts, entities)`

## Notes
- `SwapCharPosition` only swaps inside Chinese character spans.
- `HomophoneSubstitution` builds a pinyin-to-word map from packaged frequency data.
- `RandomAddDelete` samples insertion characters from packaged character-distribution data.
- `ReplaceEntity` expects entity dictionaries keyed by entity type, with offsets already aligned to the source text.
