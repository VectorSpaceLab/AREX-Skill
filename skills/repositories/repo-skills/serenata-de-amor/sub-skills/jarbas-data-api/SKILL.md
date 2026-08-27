---
name: jarbas-data-api
description: "Use Jarbas's Django REST API for reimbursements, companies,
  receipts, same-day reimbursements, applicants, and subquotas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Jarbas Data API

Use this sub-skill when you need to consume, explain, test, or debug Jarbas as the Django/DRF data browsing API for Serenata de Amor reimbursement data.

## Start here

- For endpoint paths, query parameters, response shapes, pagination, and URL examples, read [references/api-reference.md](references/api-reference.md).
- For model field families, serializer conversions, CNPJ/CPF normalization, receipt URL internals, and queryset behavior, read [references/model-and-queryset-reference.md](references/model-and-queryset-reference.md).
- For common setup/runtime failures and confusing query-result behavior, read [references/troubleshooting.md](references/troubleshooting.md).
- To build deterministic example URLs or check CNPJ/query-string behavior without network access, run [scripts/jarbas_api_probe.py](scripts/jarbas_api_probe.py).

## Fast routing

- **Build or inspect an API URL:** use `scripts/jarbas_api_probe.py build-reimbursement` or the endpoint tables in `api-reference.md`.
- **Explain missing or extra reimbursement rows:** check tuple filtering, boolean parsing, CNPJ/CPF cleaning, `receipt_url` versus `has_receipt`, `in_latest_dataset`, and PostgreSQL search notes in the references.
- **Debug serializer output:** use `model-and-queryset-reference.md` for decimal-to-float conversion, the `receipt` object, `all_numbers`, `rosies_tweet`, applicant/subquota distinct lists, and company activity nesting.
- **Debug receipt behavior:** use the receipt sections in both references and the troubleshooting guide; receipt detail may perform a network `HEAD` fetch unless the URL is already known or a non-forced miss was already fetched.
- **Need to load sample data, configure Docker/PostgreSQL, run migrations, or set environment variables:** route to the sibling `deployment-and-data-ops` sub-skill. This sub-skill only states the API-side prerequisites.
- **Need to generate Rosie suspicion/probability data:** route to `rosie-suspicion-pipeline`.
- **Need dashboard/static asset deployment:** route to `deployment-and-data-ops`.

## API-side data prerequisites

The API is read-only for anonymous users and useful only after Jarbas has reimbursement rows, optional company rows, optional suspicion/probability values, optional receipt text/URLs, and a PostgreSQL search vector populated for text search. If endpoints return valid paginated envelopes with `count: 0`, treat the API as reachable but unseeded or over-filtered; data loading is owned by `deployment-and-data-ops`.

## Verification anchors

Native behaviors represented by this sub-skill include serializer CNPJ/CPF cleaning, reimbursement list/detail/receipt view behavior, applicant and subquota distinct-list views, same-day reimbursement city enrichment, company detail responses, `manage.py check` as an API import preflight, and PostgreSQL-backed search-vector cases when that service is available.
