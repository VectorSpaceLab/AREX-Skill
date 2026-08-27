# Metadata and catalogue troubleshooting

Use the narrowest reproducible check first. Preserve the request status,
response body, resource ID/UUID, requested language, backend type, and whether
an external service was reachable. Never paste credentials or private metadata
into a report.

| Symptom | Distinguish | Next steps |
|---|---|---|
| Validator reports malformed JSON/XML | Local document syntax | Fix delimiters/encoding/XML closing tags; rerun locally. This is not a CSW outage. |
| Validator passes but `PUT` returns 422 | Schema/handler/model/index path | Fetch the live schema; compare types, required annotations, relation IDs, and `extraErrors`; retry only the corrected field. |
| `title` or `abstract` is missing from a search result | Saved value vs index freshness | Re-fetch the metadata instance, inspect the generated index/metadata XML, then run an approved narrow index/catalogue refresh. |
| `GetRecordById` returns no record after a save | Catalogue transaction or visibility | Check resource UUID, `is_published`, `advertised`, permissions, catalogue post-save logs, and backend. A private record may be intentionally hidden. |
| CSW returns connection refused/timeout | Service gate | Check the configured catalogue URL/engine, web/database readiness, remote DNS/TLS/auth, and backend capabilities. Do not rewrite valid metadata first. |
| HTTP/generic CSW returns an `ExceptionReport` | Remote protocol/capability mismatch | Capture exception code/text, confirm CSW 2.0.2 parameters and output schema, then consult the remote catalogue operator. |
| Local pycsw returns database errors | Local repository/database gate | Check PostgreSQL/PostGIS or configured database availability, migrations, pycsw mapping, and resource geometry. Local mode still needs the database. |
| Metadata XML has old values | Regeneration/preserve flag | Check `metadata_uploaded` and `metadata_uploaded_preserve`; preserved XML intentionally wins. Otherwise run a deployment-approved `regenerate_xml` operation with `--dry-run`/narrow ID first. |
| Catalogue links are absent after update | Backend record/link recreation | Check `create_record`, `get_record`, and metadata link generation. A record returned without links indicates catalogue parsing/configuration, not necessarily invalid fields. |
| Localized schema label is stale | Cache/thesaurus freshness | Confirm label thesaurus identifier/date and language code, invalidate/refresh the language cache, then fetch schema with explicit `lang`. |
| Localized field is not searchable | Index configuration | Confirm the field is in `MULTILANG_FIELDS` and the selected `METADATA_INDEXES`, check `search_lang` and PostgreSQL language mapping, then rebuild the affected index. |
| Facet count differs from resource list | Different visibility/filter state | Compare user, advertised/published state, `metadata_only`, all repeated facet filters, and `key`; reuse the facet's returned `filter` string. |
| Facet label falls back unexpectedly | Missing translation, not search failure | Confirm requested language and `ThesaurusKeywordLabel`; fallback to `alt_label` is expected when no translation exists. |
| Metadata update changes text unexpectedly | Cleaner sanitization | Inspect `extraErrors` and server logs for the cleaner handler; remove HTML/script-like content and resubmit plain text. |
| Preview/style is broken while metadata is valid | GeoServer/viewer gate | Verify resource subtype, OGC URL, GeoServer publication/style/thumbnail service, and browser separately. Do not loosen metadata checks. |

## Safe escalation order

1. Reproduce with a local file or a read-only `GET`.
2. Fetch the current schema and current instance with explicit language.
3. Validate the exact payload; preserve server error paths.
4. Check database/index/catalogue freshness in read-only or dry-run mode.
5. Check network/service/credential gates only when the deployment authorizes it.
6. Perform a narrow, reversible refresh; record the command and outcome.
7. Escalate unresolved external-service failures with the sanitized CSW
   exception/HTTP evidence.

Do not use the metadata validator as an ISO standards validator, do not run
remote CSW transactions as a smoke test, and do not claim a full catalogue
rebuild when only an instance or local XML parse was checked.
