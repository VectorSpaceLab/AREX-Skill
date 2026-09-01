# Usability case index

These review cases exercise root routing, workflow depth, bundled-script
executability, support-workflow discoverability, and troubleshooting. All
prompts are intended to be answered using only the generated runtime skill and
public package behavior; no temporary environment or live credentials are part
of a case.

## Cases

| Case path | Target | Persona/scenario | Difficulty | Primary check |
|---|---|---|---|---|
| `root/package-routing-and-version-check` | `huggingface-hub` | novice install/version/route selection | basic | root routing and safe setup |
| `sub-skills/hub-operations/private-dataset-pr-conflict` | `hub-operations` | API maintainer, stale-parent PR recovery | troubleshooting | bounded mutation recovery and redaction |
| `sub-skills/hub-operations/card-and-discussion-triage` | `hub-operations` | maintainer, cards/community read-first plan | advanced | metadata and approval gates |
| `sub-skills/hub-operations/ambiguous-upload-outcome` | `hub-operations` | automation engineer, timeout/read-after-write recovery | troubleshooting | duplicate prevention and bounded retry |
| `sub-skills/downloads-and-storage/offline-filtered-snapshot-recovery` | `downloads-and-storage` | data engineer, filtered offline snapshot | troubleshooting | dry-run/cache/offline semantics |
| `sub-skills/downloads-and-storage/bucket-prefix-safety` | `downloads-and-storage` | storage operator, prefix/traversal safety | advanced | plan and path safety |
| `sub-skills/downloads-and-storage/bucket-prefix-safety/reviewed-plan-apply-boundary` | `downloads-and-storage` | data operator, plan integrity/delete gate | troubleshooting | reviewed plan/apply boundary |
| `sub-skills/inference-and-endpoints/chat-tools-schema-fallback` | `inference-and-endpoints` | inference developer, tools/schema/async fallback | advanced | provider/task and stream safety |
| `sub-skills/inference-and-endpoints/endpoint-lifecycle-gate` | `inference-and-endpoints` | platform engineer, paid endpoint planning | troubleshooting | health/state/confirmation gate |
| `sub-skills/cli-and-automation/stdout-stderr-dry-run-delete-gate` | `cli-and-automation` | automation user, JSON/stderr/delete refusal | intermediate | CLI streams and destructive safety |
| `sub-skills/cli-and-automation/version-skew-extension-safety` | `cli-and-automation` | maintainer, executable skew/extension trust | troubleshooting | help-first version diagnosis |
| `sub-skills/hosted-compute-and-integrations/local-model-card-serialization` | `hosted-compute-and-integrations` | framework developer, local artifact safety | advanced | card/checkpoint/DDUF validation |
| `sub-skills/hosted-compute-and-integrations/job-space-config-recovery` | `hosted-compute-and-integrations` | platform engineer, mocked cloud config recovery | troubleshooting | resource state/billing/secret hygiene |
| `integration/hub-download-inference-cli` | root integration | platform developer, discovery/storage/inference/CLI composition | advanced | multi-route ownership and streams |
| `integration/model-card-upload-serialization` | root integration | model maintainer, local validation plus PR plan | advanced | integration boundaries and no mutation |

## Difficult synthetic coverage

Every generated sub-skill has two difficult synthetic cases: `hub-operations`
has conflict recovery and ambiguous upload outcomes; `downloads-and-storage` has
offline filtered recovery plus bucket prefix/path and reviewed-plan safety;
`inference-and-endpoints` has chat/schema/stream fallback and Endpoint state
gating; `cli-and-automation` has stdout/stderr/delete gating and version
skew/extension trust; `hosted-compute-and-integrations` has local artifact
recovery and shared lifecycle safety. The concrete directories above implement
both cases for every sub-skill.

The two integrated cases are synthetic compositions because the repository's
native tests cover the component APIs separately and do not provide safe,
hermetic cross-route scenarios. Their README files explain this choice and
assertions cover root-plus-sub-skill routing and no-network boundaries.

## Native anchors

Native evidence is mapped privately in
`reports/integration/native-ground-truth-candidates.md`: CLI framework/output,
URI/cache/offline, HfApi/auth/commit, cards, inference types/provider mocks,
Jobs/Sandbox models, WebhooksServer/OAuth, mixins, serialization, and DDUF
unit cases. Native cases are run only after integration; network, credentials,
production, paid, destructive, Xet-service, and large-transfer cases remain
explicitly skipped.

## Assertion summary

- Cases with `assertions.json`: 15.
- Native-evidence-anchored capabilities: all five sub-skills plus root; each
  has source docs and at least one native test/module in its assertion basis.
- Synthetic-only capabilities: integrated cross-route composition and the exact
  no-network multi-stage orchestration; their component behavior has native
  anchors but the composition is synthetic.
- Capabilities without assertions: none among the selected primary/support
  routes. Long-tail dynamic provider catalogs, live hosted services, platform
  variants, and maintainer release automation are explicitly outside selected
  case scope and listed in the long-tail register.
- Fixtures: none are copied; cases use temporary/mock/local fixtures generated
  by the future verifier so no source checkout, token, cache, or model artifact
  becomes a review dependency.
