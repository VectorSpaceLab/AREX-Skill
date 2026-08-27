# API reference

## Time
- `parse_time(time_string, time_base=..., time_type=None, ret_type='str', strict=False, virtual_time=False, ret_future=False, period_results_num=None, lunar_date=True)`
- `jio.ner.extract_time(text, time_base=..., with_parsing=True, ret_all=False, ret_type='str', ret_future=False, period_results_num=None)`

Return shapes:
- `parse_time` returns `time_point`, `time_span`, `time_period`, or `time_delta` dictionaries.
- `extract_time` returns NER-style records with `text`, `offset`, `type`, and optionally `detail`.

## Money
- `parse_money(money_string, default_unit='元', ret_format='detail')`
- `jio.ner.extract_money(text, with_parsing=True, ret_all=False, print_exception=False, use_jiojio=False)`
- `money_num2char(num, sim_or_tra='tra')`

Return shapes:
- `parse_money` returns standardized numeric amount, currency case, and definition.
- `extract_money` returns NER-style money spans.

## Location and attribution
- `parse_location(location_text, town_village=False, change2new=True)`
- `recognize_location(text, top_k='default')`
- `phone_location(text)`
- `cell_phone_location(phone_num)`
- `landline_phone_location(phone_num)`

Return shapes:
- `parse_location` returns province/city/county and optional town/village detail.
- `recognize_location` returns `domestic`, `foreign`, and `others` buckets.
- `phone_location` returns number, province, city, type, and operator when the boundary-sensitive regex matches.

## IDs, plates, and character helpers
- `parse_id_card(id_card)`
- `extract_id_card(text, detail=False)`
- `parse_motor_vehicle_licence_plate(motor_vehicle_licence_plate)`
- `extract_motor_vehicle_licence_plate(text, detail=False)`
- `pinyin(text, formater='standard'|'simple'|'detail')`
- `char_radical(text)`
- `idiom_solitaire(cur_idiom, same_pinyin=True, check_idiom=False, same_tone=True, with_prob=True, restart=False)`
- `lunar2solar(lunar_year, lunar_month, lunar_day, leap_month=False)`
- `solar2lunar(solar_date)`

## Useful notes
- `parse_time` is strict about noisy input and supports lunar dates.
- `parse_location` can expand old or shorthand locations when `change2new=True`.
- `idiom_solitaire` uses the idiom dictionary and pinyin matching, so the result can vary when `with_prob=True`.
- `pinyin` returns `<py_unk>` for unknown characters.
- `char_radical` returns default placeholder values for unknown characters.
