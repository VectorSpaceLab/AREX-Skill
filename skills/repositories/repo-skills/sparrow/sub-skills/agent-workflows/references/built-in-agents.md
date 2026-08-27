# Built-in Sparrow Agents

The built-in agent names are exact and case-sensitive:

- `medical_prescriptions`
- `trading`
- `bonds`

Unknown names are rejected by the agent manager with `Agent '<name>' not found`. Use `/api/v1/sparrow-agents/agents` before submitting jobs when the running service may have been customized.

## Quick selection table

| Agent | Preferred endpoint | Input style | External dependencies | Best use |
| --- | --- | --- | --- | --- |
| `medical_prescriptions` | `/execute/file` or `/execute/file/async` | Multipart PDF upload plus `extraction_params` JSON string | Sparrow LLM inference backend, valid `sparrow_key`, PDF tooling | Multi-page prescription/adjudication PDFs. |
| `trading` | `/execute/data` or `/execute/data/async` | JSON object with `symbols`, `account_balance`, optional `risk_tolerance` | Placeholder market client by default; no credential needed until customized | Demonstrating data-agent flow, market analysis, decision generation. |
| `bonds` | `/execute/data` | JSON object; optional `search_results_file` | Sparrow Instructor backend; Tavily only when no cached search file is supplied | Bond portfolio risk and sell/hold decision workflow. |

## `medical_prescriptions`

`medical_prescriptions` is a file-oriented workflow for multi-page medical prescription or adjudication packets. It validates the uploaded document, classifies pages through a Sparrow Parse call, converts selected pages to page images, and extracts page-type-specific data.

### Required request shape

Use multipart form data:

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/file' \
  -F 'agent_name=medical_prescriptions' \
  -F 'extraction_params={"sparrow_key":"123456"}' \
  -F 'file=@prescription.pdf;type=application/pdf'
```

`extraction_params` must be a JSON object string. The medical client reads `extraction_params.sparrow_key` and forwards it to the Sparrow LLM inference backend.

### PDF constraints and rejection reasons

The medical workflow rejects or fails early when:

- the upload is not a PDF by `content_type` and does not have a `.pdf` filename;
- the PDF has one page or zero pages; medical processing explicitly requires multiple pages;
- the PDF bytes cannot be parsed;
- `extraction_params` is malformed JSON or not an object;
- `sparrow_key` is missing from `extraction_params`;
- the configured Sparrow LLM backend is unavailable or returns a non-200 response;
- page conversion support is missing from the runtime environment;
- the classified page types do not match the configured list of page types to process, resulting in zero selected pages.

### Page routing inside the workflow

The workflow first asks the Sparrow LLM backend to classify pages with the configured `page_type` list. It then processes only page types listed in `page_type_to_process`.

Page extraction uses two page families:

- table-style pages: `adjudication_table` and `invoice_request_form`;
- details-style pages: `adjudication_details`, `application_for_coverage`, and `patient_info`.

Each family has its own query and model options in the agent configuration. Details-style pages also use the configured crop size.

### Output shape

Successful medical responses include:

```json
{
  "filename": "prescription.pdf",
  "total_pages_processed": 2,
  "results": [
    {
      "page_type": "adjudication_table",
      "extracted_data": {},
      "status": "success"
    }
  ]
}
```

Per-page extraction errors are captured as result objects with `status: "failed"` and an `error` string. Document validation errors fail the whole workflow.

## `trading`

`trading` is a data-oriented workflow. It validates a small trading request, obtains market data through a market client, calculates simple indicators, and emits trading decisions.

### Required data payload

```json
{
  "agent_name": "trading",
  "input_data": {
    "symbols": ["AAPL", "GOOGL"],
    "account_balance": 100000,
    "risk_tolerance": 0.5
  }
}
```

Rules enforced by the workflow:

- `symbols` is required and must be truthy; use a non-empty list of ticker strings.
- `account_balance` is required and must be truthy; `0` is rejected by the source validation logic.
- `account_balance` is converted to `float`.
- `risk_tolerance` is optional and defaults to `0.5`.
- `risk_tolerance` is converted to `float`; the source implementation does not clamp it, but user-facing payloads should normally keep it between `0` and `1`.

The default market client is a placeholder. It returns fixed market data for each symbol, so the built-in behavior is useful as an API/schema workflow smoke test rather than production trading logic.

### Output shape

```json
{
  "timestamp": "ISO-8601 timestamp",
  "market_analysis": {
    "AAPL": {
      "price": 100.0,
      "volume": 1000000,
      "indicators": {
        "sma_20": 100.0,
        "sma_50": 100.0,
        "volatility": 0.0
      }
    }
  },
  "trading_decisions": [
    {"symbol": "AAPL", "action": "sell", "quantity": 10.0}
  ],
  "parameters_used": {
    "symbols": ["AAPL"],
    "risk_tolerance": 0.5
  }
}
```

If the market client is customized to call a real API, document the credential source, request limits, failure modes, and response normalization before relying on production decisions.

## `bonds`

`bonds` is a data-oriented workflow for a bundled bond portfolio. It loads a positions JSON file from the agent package, analyzes risk with Sparrow Instructor, enriches positions with either cached web search results or Tavily search, and asks Sparrow Instructor for sell/hold decisions.

### Recommended cached-search payload

Use cached search results when you want to avoid Tavily credentials, network calls, or nondeterministic web search content:

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/data' \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "bonds",
    "input_data": {"search_results_file": "search_results.json"}
  }'
```

`search_results_file` is interpreted as a filename located next to the agent's cached search data. Use a simple basename such as `search_results.json` or `search_results_1.json`; do not pass an absolute path or a path with directory traversal.

### Non-cached Tavily path

If `search_results_file` is omitted, the workflow creates a Tavily client from the configured Tavily API key and searches each bond position twice:

1. historical performance since the purchase year;
2. current outlook.

The search summaries are saved as a new `search_results*.json` file without overwriting an existing cache. This path needs a real Tavily key and external network access. Prefer the cached path for smoke tests and offline operation.

### Sparrow Instructor calls

The bonds workflow calls Sparrow Instructor twice:

1. risk analysis: returns fields such as `isin`, `instrument_name`, `loss_pct`, and `risk_level`;
2. sell/hold decision: combines positions, risk analysis, and market research into decisions with reasoning.

These are LLM calls through the configured backend. If they fail, the workflow records failed/skipped status in the corresponding step and downstream decisions may be skipped.

### Output shape

```json
{
  "positions": {"extracted_data": {"positions": []}, "status": "success"},
  "risk_analysis": {"risk_analysis": {}, "status": "success"},
  "search_result": {"enriched_positions": [], "status": "success"},
  "decision": {"decisions": {}, "status": "success"}
}
```

### Async caveat

The web API registers `bonds`, but the Celery worker manager registers only `medical_prescriptions` and `trading`. Unless the worker registration has been extended, use synchronous `/execute/data` for `bonds`.
