# Native Testing Notes

This reference summarizes source-backed plugin-test behavior so future agents can choose bounded, safe verification cases. It is not an instruction to run source checkout scripts. Prefer the bundled static helper [../scripts/inspect_plugin_bundles.py](../scripts/inspect_plugin_bundles.py) for catalog inspection, then recreate only the minimum test behavior needed for the current task.

## What the native tests cover

Source evidence defines two major plugin test families:

1. **Catalog-driven plugin execution tests**
   - Generate test cases by scanning bundle and plugin schema YAML.
   - For each schema test case, POST to `/v1/execute` with `bundle_id`, `plugin_id`, `input_params`, `credentials`, and `project_id: test_project_id`.
   - Credential values are loaded from environment variables matching each bundle's credential schema.
   - `schema` mode asserts success and presence of every output-schema key.
   - `precise` mode asserts exact output values.
2. **Generated-image storage integration tests**
   - Execute `chart_maker/make_line_chart` with local, S3-with-public-domain, and S3-without-public-domain configurations.
   - Assert that execution returns an image URL.
   - Then pass the URL to OpenAI and Gemini vision plugins to verify that downstream providers can fetch/read it.

## Source-backed test exclusions

The catalog-driven source test generator excludes or skips several cases. Preserve these as safe skip criteria unless the user explicitly provisions credentials/network/quota and asks to test them.

| Excluded/skipped area | Source-backed reason or implication |
| --- | --- |
| `aftership` | Excluded from generated plugin cases. Requires external provider credentials/network. |
| `coin_market_cap` | Excluded from generated plugin cases. Requires external provider credentials/network. |
| `api_ninjas_commodity_price` | Excluded from generated plugin cases. Requires external provider credentials/network. |
| `geospy_api` | Excluded from generated plugin cases. Requires external provider credentials/network and image fetch. |
| `weather_bit` | Excluded from generated plugin cases. Requires external provider credentials/network. |
| `duckduckgo` | Excluded from generated plugin cases despite no credentials; external service behavior is non-deterministic. |
| `stability_ai` | Skipped at execution test time. Requires provider credentials/quota and image generation. |
| `webpilot/internet_search_4_02_16k` | Skipped at execution test time. |
| `exchangerate_api/get_historical_exchange_rate` | Excluded from generated cases. |
| `gemini_vision_models/chat_completion_by_gemini_1_0_pro` | Excluded from generated cases. |

## Safe bounded verification cases

### Case A: precise no-credential arithmetic

Use this when the task needs a deterministic plugin execution check without network, credentials, image storage, or backend object lifecycle.

Payload core:

```json
{
  "bundle_id": "arithmetic",
  "plugin_id": "add",
  "input_params": {"number_1": 1, "number_2": 2},
  "credentials": {}
}
```

Assertions:

- HTTP/service response is successful.
- Nested plugin status is `200`.
- Nested data contains `result: 3`.

Additional precise examples from source schema:

- `add`: `-123 + 200 -> 77`; `5.123 + 5.876 -> 10.999`
- `divide`: `1 / 2 -> 0.5`; `0 / -12.12 -> 0`
- `divide` with `number_2 = 0` should be treated as an error path, not a precise success case.

### Case B: schema-only generated image with local storage

Use this when the task specifically covers image URL generation and local storage.

Payload core:

```json
{
  "bundle_id": "chart_maker",
  "plugin_id": "make_bar_chart",
  "project_id": "test_project",
  "input_params": {
    "x_values": ["A", "B", "C"],
    "y_values": [10, 20, 30]
  },
  "credentials": {}
}
```

Assertions:

- Service response is successful.
- Nested plugin status is `200`.
- Nested data contains `url`.
- Under local storage, `url` starts with the configured `HOST_URL` and should include the generated `imgs/p/<project_id>/...` path when file-category inclusion is enabled.

Skip if image-rendering dependencies, writable local volume, or plugin service storage configuration are not available. Do not upgrade this into downstream OpenAI/Gemini vision validation unless those provider credentials and quotas are explicitly provided.

### Case C: S3 URL formation without downstream provider calls

Use this when the task is to diagnose S3 configuration rather than provider image content.

Assertions:

- Service starts only when required S3 variables are set.
- If `S3_BUCKET_PUBLIC_DOMAIN` is set, returned URL begins with that public domain.
- If `S3_BUCKET_PUBLIC_DOMAIN` is not set, returned URL falls back to `S3_ENDPOINT/S3_IMAGE_BUCKET_NAME`.
- Local temporary file should not remain after successful upload.

Skip if no S3-compatible test bucket, endpoint, and credentials are available. This is an optional integration case, not required for no-credential plugin selection.

## Native-test safety levels

| Test type | Safety | Required resources | When to use |
| --- | --- | --- | --- |
| Static catalog inspection | Safe | Local checkout only, no service needed | Always safe for drift/count/schema checks. |
| Arithmetic precise execution | Safe if service is already running | Plugin service, no credentials | Best synthetic workflow execution check. |
| Random/time/web/search no-credential plugins | Bounded but external | Plugin service and network | Only when non-deterministic external behavior is acceptable. |
| Chart/QR local storage | Bounded local integration | Plugin service, image deps, writable volume, local storage env | Storage troubleshooting and generated image URL validation. |
| S3 storage | External integration | S3-compatible endpoint, bucket, credentials | S3 URL/upload diagnosis. |
| Credentialed providers | External and quota-bearing | Provider credentials, network, quota | Only when the user explicitly provides/authorizes credentials and costs. |
| Downstream vision URL validation | External and quota-bearing | OpenAI/Gemini credentials, network, quota | Only for end-to-end image accessibility validation. |

## Safe skip criteria

Skip or mark blocked, rather than failing the skill/task, when:

- Required provider API keys are absent, placeholder, expired, quota-limited, or not authorized for the selected provider.
- External network access is unavailable or intentionally disabled.
- The task only asks for catalog/schema payload selection and does not require provider execution.
- Image-rendering dependencies are unavailable and the selected plugin does not need generated image output.
- `OBJECT_STORAGE_TYPE=s3` is selected but the S3 endpoint, access key, secret, or image bucket is intentionally not provisioned.
- Local storage is selected but the service has no writable volume or no externally reachable `HOST_URL`.
- Downstream OpenAI/Gemini validation is not in scope; a generated URL can still be checked structurally without calling those providers.

## Verification focus for difficult usability cases

- **No-credential synthetic tool selection:** Demonstrate why `arithmetic/add` is the safest plugin, list its required numeric inputs, expected numeric output, and no-credential `{}` credential payload.
- **Local versus S3 image URL diagnosis:** Compare the expected URL prefix/path under local storage against S3 storage. Tie failures to `OBJECT_STORAGE_TYPE`, `HOST_URL`, `PATH_TO_VOLUME`, `S3_ENDPOINT`, `S3_IMAGE_BUCKET_NAME`, and `S3_BUCKET_PUBLIC_DOMAIN` before attributing them to chart or QR-code handler logic.
