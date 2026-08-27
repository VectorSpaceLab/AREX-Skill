# AppAgent API reference

This reference summarizes the source-level helpers that the generated skill routes through. The repo is script-driven, so these APIs are the real runtime surface.

## Config

### `load_config(config_path='./config.yaml')`
- Defined in `scripts/config.py`.
- Returns a dict built from environment variables updated with YAML values.
- Because the YAML is applied last, the file contents override matching environment keys.

## Model backends

### `BaseModel.get_model_response(prompt, images)`
- Abstract contract for multimodal backends.
- Returns `(success: bool, response_text: str)`.

### `OpenAIModel(base_url, api_key, model, temperature, max_tokens)`
- Uses OpenAI-compatible chat completions.
- `get_model_response(prompt, images)` builds a `messages=[{"role": "user", "content": ...}]` payload.
- Images are encoded as `data:image/jpeg;base64,...` URLs.
- On success, prints an estimated request cost from the token counts.
- On failure, returns `(False, error_message)`.

### `QwenModel(api_key, model)`
- Uses `dashscope.MultiModalConversation.call(...)`.
- `get_model_response(prompt, images)` returns `(True, response_text)` or `(False, error_message)`.

## Response parsers

### `parse_explore_rsp(rsp)`
Parses the exploration/deployment action format.

Expected fields in `rsp`:
- `Observation: ...`
- `Thought: ...`
- `Action: ...`
- `Summary: ...`

Returns:
- `['FINISH']`
- `['tap', area, summary]`
- `['text', text_input, summary]`
- `['long_press', area, summary]`
- `['swipe', area, direction, dist, summary]`
- `['grid']`
- `['ERROR']` on parse failure or unsupported action.

### `parse_grid_rsp(rsp)`
Parses grid-overlay actions.

Returns:
- `['FINISH']`
- `['tap_grid', area, subarea, summary]`
- `['long_press_grid', area, subarea, summary]`
- `['swipe_grid', start_area, start_subarea, end_area, end_subarea, summary]`
- `['grid']`
- `['ERROR']` on parse failure.

### `parse_reflect_rsp(rsp)`
Parses the reflection step used during autonomous exploration.

Expected decisions:
- `INEFFECTIVE`
- `BACK`
- `CONTINUE`
- `SUCCESS`

Returns:
- `['INEFFECTIVE', thought]`
- `['BACK', thought, documentation]`
- `['CONTINUE', thought, documentation]`
- `['SUCCESS', thought, documentation]`
- `['ERROR']` on parse failure.

## Android controller

### `execute_adb(adb_command)`
Runs a shell adb command and returns stripped stdout or `ERROR`.

### `list_all_devices()`
Returns the device ids reported by `adb devices`.

### `get_id_from_element(elem)`
Builds a stable-ish UI-element identifier from resource id, class, bounds, and content description.

### `traverse_tree(xml_path, elem_list, attrib, add_index=False)`
Walks a UIAutomator XML file and appends `AndroidElement` objects whose attribute matches `attrib`.

### `AndroidController(device)`
Device wrapper around adb.

Important methods:
- `get_device_size()`
- `get_screenshot(prefix, save_dir)`
- `get_xml(prefix, save_dir)`
- `back()`
- `tap(x, y)`
- `text(input_str)`
- `long_press(x, y, duration=1000)`
- `swipe(x, y, direction, dist='medium', quick=False)`
- `swipe_precise(start, end, duration=400)`

Notes:
- `get_device_size()` returns the `map(int, ...)` object from the adb output, so unpack it immediately or convert it to a tuple before reusing it.
- `get_screenshot()` and `get_xml()` return a saved path on success or `ERROR` on failure.

### Important runtime caveat
`swipe_precise()` currently constructs `adb shell input swipe {start_x} {start_x} {end_x} {end_y}`. The second coordinate should almost certainly be `start_y`, so precise grid swipes are a known bug surface.

## Utility helpers

### `print_with_color(text, color='')`
Prints a colored terminal message using `colorama`.

### `draw_bbox_multi(img_path, output_path, elem_list, record_mode=False, dark_mode=False)`
Writes a labeled screenshot with numbered element overlays.

### `draw_grid(img_path, output_path)`
Overlays a grid on a screenshot and returns `(rows, cols)`.

### `encode_image(image_path)`
Reads an image and returns a base64 string for OpenAI-style image payloads.
