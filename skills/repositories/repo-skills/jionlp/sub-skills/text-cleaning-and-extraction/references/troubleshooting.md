# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `remove_phone_number` or `extract_phone_number` misses a number | The regex expects a non-digit boundary around the match | Use the full surrounding text, or normalize the string so the number is not glued to other digits. |
| `clean_html` drops more than expected | The HTML is malformed or contains menu/navigation blocks | Try `clean_text` first, or inspect the cleaned `meta_info` separately. |
| `write_file_by_line` raises a `TypeError` | The input list contains an unsupported element type | Convert the item to `str`, `list`, `dict`, `set`, `int`, or `float` before writing. |
| `read_file_by_*` returns blank or truncated data | The file is not UTF-8 or the line limit is too small | Re-open as UTF-8 and raise `line_num` or disable line skipping if needed. |
| `split_sentence` joins or splits quotes oddly | The sentence contains nested quotes or punctuation edge cases | Use the result as a heuristic split and review quoted spans manually when the output matters. |
| `remove_stopwords` removes too much | The filter flags time/location/number/non-Chinese tokens aggressively | Disable the extra filters first, then re-enable them one at a time. |
