# API reference

## Cleaning and normalization
- `clean_text(text, remove_html_tag=True, convert_full2half=True, remove_exception_char=True, remove_url=True, remove_redundant_char=True, remove_parentheses=True, remove_email=True, remove_phone_number=True, delete_prefix=False, redundant_chars=None) -> str`
- `clean_html(orig_html_text) -> (content, meta_info)`
- `remove_html_tag(text) -> str`
- `remove_exception_char(text) -> str`
- `remove_redundant_char(text, redundant_chars=None) -> str`
- `convert_full2half(text) -> str`

## Pattern extraction / replacement
- `extract_email(text, detail=False)`
- `extract_url(text, detail=False)`
- `extract_phone_number(text, detail=False)`
- `extract_ip_address(text, detail=False)`
- `extract_id_card(text, detail=False)`
- `extract_qq(text, detail=False, strict=True)`
- `extract_wechat_id(text, detail=False)`
- `extract_parentheses(text, parentheses='{}「」[]【】()（）<>《》〈〉『』〔〕｛｝＜＞〖〗', detail=False)`
- `extract_motor_vehicle_licence_plate(text, detail=False)`
- `remove_email(text, delete_prefix=False)`
- `remove_url(text)`
- `remove_phone_number(text, delete_prefix=False)`
- `remove_ip_address(text)`
- `remove_id_card(text)`
- `remove_qq(text)`
- `remove_parentheses(text)`
- `replace_email(text, token='<email>')`
- `replace_url(text, token='<url>')`
- `replace_phone_number(text, token='<tel>')`
- `replace_ip_address(text, token='<ip>')`
- `replace_id_card(text, token='<id>')`
- `replace_qq(text, token='<qq>')`
- `replace_chinese(text, token='<chinese>')`
- `extract_chinese(text)`

## Checks and sentence splitting
- `check_any_chinese_char(text) -> bool`
- `check_all_chinese_char(text) -> bool`
- `check_any_arabic_num(text) -> bool`
- `check_all_arabic_num(text) -> bool`
- `split_sentence(text, criterion='coarse'|'fine') -> list[str]`
- `remove_stopwords(text_segs, remove_time=False, remove_location=False, remove_number=False, remove_non_chinese=False, save_negative_words=False) -> list[str]`

## File helpers
- `read_file_by_iter(file_path, line_num=None, skip_empty_line=True, strip=True, auto_loads_json=True)`
- `read_file_by_line(file_path, line_num=None, skip_empty_line=True, strip=True, auto_loads_json=True)`
- `write_file_by_line(data_list, file_path, start_line_idx=None, end_line_idx=None, replace_slash_n=True)`
- `TimeIt(name=...)`
- `zip_file(...)` and `unzip_file(...)`

## Notes
- `extract_*` and `replace_*` helpers use boundary-sensitive regexes.
- `clean_html` is the HTML-specific path; `clean_text` is the broader normalization path.
- `remove_stopwords` expects tokenized input, not a raw string.
