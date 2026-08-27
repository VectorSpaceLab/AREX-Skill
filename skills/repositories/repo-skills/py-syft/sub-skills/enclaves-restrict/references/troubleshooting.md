# Enclave and restrict troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Runner refuses to start | Required env vars missing or `REQUIRE_TEE=true` outside TEE. | Render/check env; use false only for local development. |
| Job never runs | One or more data owners have not approved. | Check owner list and approval state. |
| Attestation signature fails | Invalid token, missing network/JWKS access, wrong audience, expired beyond grace. | Do not trust; re-fetch token or fix environment. |
| Debug enabled | Confidential VM in debug mode. | Reject for production. |
| Image digest skipped | `expected_image_digest` unset. | Pin digest for production appraisal. |
| `MarkerError` | Missing/mismatched/empty syft-restrict markers. | Add balanced markers around private code. |
| Restrict violation | Private region uses banned construct, operator, or call. | Move public wrappers outside private region or adjust explicit allow policy. |
