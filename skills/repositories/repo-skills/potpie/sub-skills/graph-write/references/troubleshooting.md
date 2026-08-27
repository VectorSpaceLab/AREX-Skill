# Graph write troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `graph propose` rejects the payload | Invalid label/action, missing required fields, nested legacy wrapper, or bad scope/source reference. | Generate `graph mutation-template`, flatten the payload, add required fields, and retry proposal. |
| Proposal reports review required | Mutation is risky, ambiguous, destructive, or low-confidence. | Obtain explicit user approval or add evidence/scope to reduce risk; do not commit blindly. |
| Plan expired before commit | Plan TTL or graph state changed. | Re-run `graph propose` against the current graph and compare warnings before committing. |
| Commit fails verification | Applied state did not match expected graph condition. | Inspect `graph history`, `graph describe`, and quality report; do not reapply the same plan without understanding drift. |
| `graph mutate` works differently than propose/commit | Legacy wrapper path may bypass or compress plan details. | Prefer propose/commit unless compatibility is the user's explicit goal. |
| Bulk apply partially succeeds | Chunk-level failure, duplicate operation, or validation error. | Preserve per-item output, retry only failed items after correction, and confirm history/read state. |
| Inbox item cannot be approved or cleared | Item state changed, missing permissions, or stale graph reference. | Inspect inbox item details and graph history before changing state. |
| Quality report suggests many fixes | Graph has stale/duplicate/weak records or missing verification data. | Prioritize high-confidence repairs; avoid automated broad cleanup without user approval. |
| Nudge output is weak or irrelevant | Source graph evidence is missing or too broad. | Run a read-side query first, narrow scope, or create better evidence before nudging. |

## Malformed mutation checklist

1. Regenerate the template for the intended entity/record kind.
2. Remove nested wrappers unless the CLI template requires them.
3. Confirm required fields: action/kind, entity key or identity fields, description, scope, source/evidence, and validation metadata where supported.
4. Confirm enum values against the installed graph contract if the skill may be stale.
5. Retry `graph propose` and inspect warnings before commit.

## Approval and verification rules

- Review-required means the system intentionally stopped before applying a potentially unsafe change.
- Approval should be tied to the exact plan id and payload, not a general statement such as "do it" from earlier context.
- Use verification flags/options when available, especially after quality repairs, bulk writes, or writes derived from ambiguous reads.
- If verification degrades, capture the degraded condition in the handoff instead of hiding it.

## Recovery order after a failed write

1. Stop applying more writes.
2. Inspect plan/commit output.
3. Run `potpie graph history` for the affected scope.
4. Run `potpie graph quality report` if state may be inconsistent.
5. Use `graph-read` to confirm entity state.
6. Author a corrected proposal or ask the user whether to abandon/repair.
