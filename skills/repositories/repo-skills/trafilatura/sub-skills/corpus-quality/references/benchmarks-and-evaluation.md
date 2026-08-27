# Benchmarks And Evaluation

Use this reference to choose an evaluation level. Most corpus-quality tasks do **not** need Trafilatura's full benchmark comparison. Start with the bundled no-network smoke and representative output validation; escalate to native unit tests or benchmark gates only when the task changes extraction behavior or needs published-score context.

## Evaluation levels

| Level | When to use | Environment | Typical scope |
| --- | --- | --- | --- |
| Bundled smoke | Any agent using this sub-skill wants a quick sanity check for deduplication and TEI/structured output assumptions. | Installed Trafilatura package and base dependencies; no network. | `scripts/corpus_quality_smoke.py`. |
| Corpus sample validation | A user is building a web corpus and needs confidence before scaling. | User's sample HTML pages or extracted records; no source checkout required. | Parse JSON/CSV/XML/XML-TEI, count missing metadata, inspect duplicate clusters. |
| Safe native validation class | A Trafilatura source checkout is available and the user is validating package behavior, not just using it. | Development/test environment; no competitor benchmark extras for the safe class. | Deduplication unit class, XML/TEI unit class, selected output-conversion unit class. |
| Quality gate | A change to Trafilatura extraction behavior may affect benchmark F1. | Trafilatura installed with the `all` extra in a source checkout containing the eval corpus. | Own-benchmark gate using fast and fallback Trafilatura runners. |
| Full benchmark comparison | A user explicitly asks to compare extractors or reproduce published benchmark tables. | Trafilatura installed with the `eval` extra; optional competitor packages; benchmark corpus; often slow. | Competitor extractor comparison, result tables, skip/error reporting. |

## Safe default: bundled smoke

From this sub-skill directory, run:

```bash
python scripts/corpus_quality_smoke.py
```

The smoke is intentionally small and offline. It checks:

- deterministic content fingerprints;
- Simhash similarity ordering and `existing_hash` reuse;
- exact `duplicate_test()` behavior with strict options;
- JSON and CSV parseability for a tiny HTML fixture;
- XML-TEI parseability and TEI validation when the installed package can produce it.

If this fails, treat it as an environment or package-contract problem before running heavier tests.

## Corpus sample validation without native tests

For a user's corpus, validate a sample of actual pages or records. This is usually more useful than the upstream benchmark because it matches the target domain.

```python
import csv
import json
from io import StringIO
from lxml import etree
from trafilatura import extract
from trafilatura.deduplication import Simhash
from trafilatura.xml import validate_tei

sample_results = []
seen = []
for record_id, url, html in sample_pages:
    txt = extract(html, url=url, record_id=record_id, output_format="txt", include_comments=False, deduplicate=True)
    js = extract(html, url=url, record_id=record_id, output_format="json", with_metadata=True)
    tei = extract(html, url=url, record_id=record_id, output_format="xmltei", with_metadata=True, tei_validation=True)

    assert txt is None or isinstance(txt, str)
    if js:
        assert json.loads(js).get("text")
    if tei:
        tree = etree.fromstring(tei.encode("utf-8"))
        assert validate_tei(tree) is True

    if txt:
        h = Simhash(txt)
        sample_results.append((record_id, max((h.similarity(prev) for prev in seen), default=0.0)))
        seen.append(h)
```

Track these metrics per batch:

- extraction success rate;
- metadata coverage rates (`title`, `date`, `author`, `source`, `fingerprint`);
- `None` results caused by strict metadata filtering;
- parse/validation failures by output format;
- exact duplicate drops versus near-duplicate clusters;
- comment-inclusion policy.

## Safe native validation class

When a source checkout is available and native validation is selected by the integrator/user, the safe corpus-quality class covers:

- deduplication unit behavior: fingerprints, Simhash, LRU cache, duplicate body drops, cache reset;
- XML/TEI unit behavior: header construction, TEI repair, valid/invalid TEI checks, heading/list/table edge cases;
- selected output conversion unit behavior: CSV field order, JSON metadata fields, XML/XML-TEI serialization.

These are safe because they are local, unit-sized, and do not require competitor extractor packages or live network access. They are still source-checkout validation, not a dependency for using this runtime skill.

## Quality gate context

The quality gate scores Trafilatura itself on the bundled evaluation corpus and fails if F1 drops below pinned floors. It is appropriate when changing extraction logic, deduplication, formatting, or benchmark annotations.

Source-checkout-only setup context:

- Use an environment with Trafilatura's `all` extra for quality-gate parity.
- Select the upstream quality-gate runner only when a separate native-verification plan authorizes source-checkout benchmark execution.
- Treat the upstream gate runner as reference-only from this runtime skill; the bundled smoke and user-sample validation above are the self-contained checks.

Important properties:

- It uses Trafilatura-only runners (`fast` and fallback/balanced) with comments off, tables on, and formatting off.
- It reads the eval annotations and HTML inputs, validates the annotation structure, and computes precision/recall/accuracy/F1 from required (`with`) and forbidden (`without`) chunks.
- The corpus fingerprint covers annotation data and resolved HTML inputs, so changed corpus data must be re-pinned.
- `--update` re-measures and re-pins; it refuses to lower a floor unless `--allow-regression` is explicitly supplied.
- A plain install can score slightly differently on non-UTF-8 pages; use the `all` extra for gate parity.

Do not use the gate as a generic web-corpus quality score. It tests the package against a handcrafted benchmark, not the user's domain distribution.

## Full benchmark comparison context

The full comparison evaluates Trafilatura and alternative extractors. It is reference-only unless the user explicitly asks for benchmark reproduction or extractor comparison.

Source-checkout-only setup context:

- Use an environment with Trafilatura's `eval` extra for full competitor comparison.
- Download NLTK `punkt` and `punkt_tab` once if the `news-please` competitor is selected.
- Prefer the small comparison mode when only Trafilatura and baselines are needed; reserve the all-algorithm mode for explicit benchmark-reproduction tasks.
- Treat the upstream full benchmark runner as reference-only from this runtime skill; it is not required for ordinary corpus construction.

Boundaries and skip behavior:

- Competitor libraries are imported by the individual runner that needs them. A missing/unimportable competitor is reported and skipped rather than aborting the whole comparison.
- `magic-html` requires Python 3.12 or later and is skipped on older versions.
- `news-please` needs NLTK tokenizer data (`punkt`, `punkt_tab`) to avoid repeated network attempts per document.
- The benchmark is handcrafted with/without segment scoring and does not directly evaluate duplicate segment removal or document ordering.
- Full comparison can install many packages and take materially longer than native unit checks.

## Test-selection guidance

Choose the smallest level that answers the user's question:

1. **Using Trafilatura to build a corpus:** run the bundled smoke, then validate the user's own sample records. Avoid native source tests unless package correctness is questioned.
2. **Debugging duplicate boilerplate or invalid TEI in user data:** run the bundled smoke, then construct a small reproduction from the user's HTML. Do not jump to full benchmark comparison.
3. **Changing Trafilatura internals or verifying a generated repo skill:** safe native validation class first; add the quality gate if extraction/serialization behavior changed.
4. **Publishing/reproducing benchmark numbers:** use the quality gate for Trafilatura-only regression and full comparison only with explicit benchmark scope, extras, and time budget.
5. **No source checkout or no optional extras:** do not block corpus use; rely on the self-contained smoke and sample validation, and mark benchmark/native checks as not selected.
