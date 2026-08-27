# Plugin Bundle Catalog

This reference is distilled from the plugin service's bundle, plugin, cache, model, and test evidence. It is intended to let a future agent select a bundle/plugin and build a correct payload without reading source files.

## Verified catalog snapshot

- Built-in bundles: **47**
- Built-in plugins: **86**
- No-credential bundles: **13**
- Credentialed bundles: **34**
- Verified Python 3.10 imports: `APIRouter`, `Bundle`, `Plugin`, `Arithmetic`, `ChartMaker`

Catalog schemas use two layers:

- Bundle schema: `plugin/bundles/<bundle_id>/resources/bundle_schema.yml` as source evidence.
- Plugin schema: `plugin/bundles/<bundle_id>/plugins/<plugin_id>/plugin_schema.yml` as source evidence.

Use the bundled static helper [../scripts/inspect_plugin_bundles.py](../scripts/inspect_plugin_bundles.py) to inspect the same schema layout in a local checkout. The helper performs static file reads only; it does not import the service, contact providers, or load credentials.

## Runtime object model

### Bundle

A bundle record has:

| Field | Meaning |
| --- | --- |
| `bundle_id` | Stable id such as `arithmetic` or `chart_maker`. |
| `provider` | Provider label shown in catalog responses. |
| `developer` | Developer label. |
| `name` / `description` | Usually i18n keys resolved by the service for the requested `lang`. |
| `credentials_schema` | Map of accepted credential names to `{type, description, secret, required}`. Empty means no credentials are required. |
| `icon_url` | Built from the configured icon URL prefix plus `/images/plugins/bundles/icons/<bundle_id>.png`. |

Bundle filters are applied at startup through `ALLOWED_BUNDLES` and `FORBIDDEN_BUNDLES`. A missing expected bundle can be a deployment/configuration filter rather than a code problem.

### Plugin

A plugin record has:

| Field | Meaning |
| --- | --- |
| `bundle_id` | Parent bundle id. |
| `plugin_id` | Stable plugin id within the bundle. |
| `name` / `description` | Usually i18n keys resolved by the service for the requested `lang`. |
| `input_schema` | Map from input key to `{type, name, description, required}`. |
| `output_schema` | Map from output key to `{type, name, description, required}`. |

Supported schema types are:

- Scalars: `string`, `integer`, `number`, `boolean`
- Arrays: `string_array`, `integer_array`, `number_array`, `boolean_array`
- URL strings: `image_url`, `file_url`

Execution input validation is strict for declared fields: required fields must be present; numeric arrays must be Python/JSON lists of numbers; image/file URLs must be strings beginning with `http`. Extra input keys are not rejected by schema validation, but plugin handlers usually ignore keys they do not read.

## No-credential bundles for safe synthetic workflows

These are the best choices when a task should avoid provider credentials. Some still need network access or image storage; check the notes.

| Bundle | Plugins | Notes |
| --- | ---: | --- |
| `arithmetic` | 4 | Best fully local synthetic tool path. Precise tests exist for add/subtract/multiply/divide. |
| `arxiv_search` | 1 | No credentials, but searches external arXiv service. |
| `calculator` | 1 | Expression evaluation utility; inspect schema before accepting arbitrary expressions. |
| `chart_maker` | 6 | No credentials but requires `project_id`, image rendering dependencies, and local/S3 storage. |
| `duckduckgo` | 2 | No credentials, external search; native tests skip it. |
| `jina_web_reader` | 1 | No credentials, external URL reading. |
| `jobicy` | 1 | No credentials, external jobs API. |
| `qr_code_generator` | 1 | No credentials but requires `project_id` and local/S3 storage for generated image URL. |
| `random_number_generator` | 1 | Local random integer generation. Good safe non-deterministic schema test. |
| `stack_overflow` | 1 | No credentials, external Stack Overflow search. |
| `time_api` | 3 | No credentials, external time API. |
| `web_reader` | 1 | No credentials, external web page fetch. |
| `wikipedia` | 1 | No credentials, external Wikipedia search. |

### Recommended no-credential synthetic case: `arithmetic/add`

Use this when the goal is to demonstrate a built-in plugin tool call without external credentials or storage.

Request payload core:

```json
{
  "bundle_id": "arithmetic",
  "plugin_id": "add",
  "input_params": {
    "number_1": 1,
    "number_2": 2
  },
  "credentials": {}
}
```

Expected schema:

| Direction | Key | Type | Required | Expected behavior |
| --- | --- | --- | --- | --- |
| input | `number_1` | `number` | yes | First operand. |
| input | `number_2` | `number` | yes | Second operand. |
| output | `result` | `number` | schema-required status is not set in one source schema, but output contains the sum. |

Expected successful result data contains `result: 3` for `1 + 2`. Other source-backed precise examples include `-123 + 200 = 77` and `5.123 + 5.876 = 10.999`.

### Safe edge case: `arithmetic/divide`

`divide` has the same two required numeric inputs and returns numeric `result`. It explicitly raises a provider-style error when `number_2` is `0`; use that edge to test error propagation.

## Generated-image no-credential cases

Use these only when storage configuration is in scope.

### `chart_maker/make_bar_chart`

Required inputs:

| Key | Type | Required | Notes |
| --- | --- | --- | --- |
| `x_values` | `string_array` | yes | Labels. |
| `y_values` | `number_array` | yes | Must have the same length as `x_values`. |
| `title` | `string` | no | Defaults to `Bar Chart`. |
| `x_title` | `string` | no | Defaults to `x`. |
| `y_title` | `string` | no | Defaults to `y`. |

Other execution requirements:

- `project_id` is required even though it is not part of `input_params`.
- Output schema contains `url` as a string.
- The handler renders a Plotly image, saves a PNG through the plugin image-storage service, then returns the stored URL.
- A length mismatch between `x_values` and `y_values` is a provider error.

### `qr_code_generator/generate_qr_code`

Required inputs:

| Key | Type | Required | Notes |
| --- | --- | --- | --- |
| `text` | `string` | yes | Encoded into a QR image. |

Other execution requirements:

- `project_id` is required.
- Output schema contains `url` as a string.
- The handler generates a PNG and stores it through the same local/S3 helper used by chart plugins.

## Full bundle summary

| Bundle | Plugins | Credentials |
| --- | ---: | --- |
| `aftership` | 1 | `AFTERSHIP_API_KEY` |
| `alpha_vantage` | 2 | `ALPHA_VANTAGE_API_KEY` |
| `api_ninjas_commodity_price` | 1 | `API_NINJAS_API_KEY` |
| `arithmetic` | 4 | none |
| `arxiv_search` | 1 | none |
| `bigbook_api` | 2 | `BIGBOOK_API_API_KEY` |
| `bing_search` | 1 | `BING_SEARCH_API_KEY` |
| `calculator` | 1 | none |
| `calorie_ninjas` | 2 | `CALORIE_NINJAS_API_KEY` |
| `chart_maker` | 6 | none |
| `coin_market_cap` | 2 | `COIN_MARKET_CAP_API_KEY` |
| `dalle_3` | 1 | `OPENAI_API_KEY` |
| `duckduckgo` | 2 | none |
| `exchangerate_api` | 3 | `EXCHANGERATE_API_API_KEY` |
| `finance_news` | 1 | `FINANCE_NEWS_API_KEY` |
| `fire_crawl` | 1 | `FIRE_CRAWL_API_KEY` |
| `gemini_vision_models` | 2 | `GOOGLE_GEMINI_API_KEY` |
| `geospy_api` | 1 | `GEOSPY_API_API_KEY` |
| `github` | 1 | `GITHUB_API_KEY` |
| `google_search` | 1 | `GOOGLE_CUSTOM_SEARCH_API_KEY`, `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` |
| `gpt_vision_models` | 2 | `OPENAI_API_KEY` |
| `jina_web_reader` | 1 | none |
| `jobicy` | 1 | none |
| `multion` | 1 | `MULTION_API_KEY` |
| `nasa` | 1 | `NASA_API_KEY` |
| `news_api` | 2 | `NEWS_API_API_KEY` |
| `nytimes` | 2 | `NEW_YORK_TIMES_API_KEY` |
| `open_weather` | 3 | `OPEN_WEATHER_API_KEY` |
| `perplexity` | 1 | `PERPLEXITY_API_KEY` |
| `pexels` | 2 | `PEXELS_API_KEY` |
| `pub_med` | 1 | `PUB_MED_API_KEY` |
| `qr_code_generator` | 1 | none |
| `random_number_generator` | 1 | none |
| `serp_api` | 2 | `SERP_API_API_KEY` |
| `serper` | 7 | `SERPER_API_KEY` |
| `spoonacular` | 1 | `SPOONACULAR_API_KEY` |
| `stability_ai` | 1 | `STABILITY_AI_API_KEY` |
| `stack_overflow` | 1 | none |
| `time_api` | 3 | none |
| `tmdb` | 5 | `TMDB_API_KEY` |
| `trip_advisor` | 2 | `TRIP_ADVISOR_API_KEY` |
| `weather_bit` | 3 | `WEATHER_BIT_API_KEY` |
| `web_reader` | 1 | none |
| `webpilot` | 2 | `WEBPILOT_API_KEY` |
| `wikipedia` | 1 | none |
| `wolfram_alpha` | 1 | `WOLFRAM_ALPHA_APP_ID` |
| `youtube` | 1 | `GOOGLE_API_KEY` |

## Plugin inventory by bundle

- `aftership`: `get_tracking_info`
- `alpha_vantage`: `get_historical_stock_data`, `get_latest_stock_data`
- `api_ninjas_commodity_price`: `get_commodity_price`
- `arithmetic`: `add`, `divide`, `multiply`, `subtract`
- `arxiv_search`: `arxiv_search`
- `bigbook_api`: `book_search`, `similar_books`
- `bing_search`: `web_search`
- `calculator`: `evaluate`
- `calorie_ninjas`: `get_nutrition_info`, `get_recipe`
- `chart_maker`: `make_2d_histogram`, `make_bar_chart`, `make_histogram`, `make_line_chart`, `make_pie_chart`, `make_scatter_plot`
- `coin_market_cap`: `get_historical_coin_data`, `get_latest_coin_data`
- `dalle_3`: `generate_image`
- `duckduckgo`: `search_image`, `search_text`
- `exchangerate_api`: `get_exchange_rate`, `get_historical_exchange_rate`, `list_exchange_rates`
- `finance_news`: `finance_news_search`
- `fire_crawl`: `scrape_web`
- `gemini_vision_models`: `chat_completion_by_gemini_1_0_pro`, `chat_completion_by_gemini_1_5_pro`
- `geospy_api`: `image_geolocate_predict`
- `github`: `search_repositories`
- `google_search`: `web_search`
- `gpt_vision_models`: `chat_completion_by_gpt4_o`, `chat_completion_by_gpt4_turbo`
- `jina_web_reader`: `read_url`
- `jobicy`: `job_search`
- `multion`: `webpage_retrieve`
- `nasa`: `get_apod_information`
- `news_api`: `get_top_headlines`, `search_news_article`
- `nytimes`: `news_search`, `top_stories_search`
- `open_weather`: `get_current_weather`, `get_daily_forecast`, `get_hourly_forecast`
- `perplexity`: `get_answer_from_perplexity`
- `pexels`: `image_search`, `video_search`
- `pub_med`: `biomedical_search`
- `qr_code_generator`: `generate_qr_code`
- `random_number_generator`: `generate_random_integers`
- `serp_api`: `get_flight_information`, `get_jobs_information`
- `serper`: `image_search`, `maps_search`, `news_search`, `scholar_search`, `shopping_search`, `text_search`, `video_search`
- `spoonacular`: `recipe_search`
- `stability_ai`: `generate_image`
- `stack_overflow`: `stack_overflow_search`
- `time_api`: `get_time_by_geo_coordinates`, `get_time_by_timezone`, `list_timezones`
- `tmdb`: `discover_movie`, `movie_search`, `movie_trends`, `now_playing`, `upcoming_movie`
- `trip_advisor`: `location_details`, `search_location`
- `weather_bit`: `get_current_weather`, `get_historical_weather`, `get_weather_forecast`
- `web_reader`: `read_web_page`
- `webpilot`: `internet_search_3_52_16k`, `internet_search_4_02_16k`
- `wikipedia`: `wikipedia_search`
- `wolfram_alpha`: `query`
- `youtube`: `search_video`
