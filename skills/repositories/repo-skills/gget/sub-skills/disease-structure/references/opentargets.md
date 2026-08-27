# Open Targets reference

`gget.opentargets` sends a GraphQL request to the public Open Targets Platform
using an Ensembl gene ID. It needs network access but no credential. The live
signature is:

```python
gget.opentargets(
    ensembl_id: str, resource: str = "diseases", limit: int | None = None,
    verbose: bool = True, wrap_text: bool = False,
    filters: dict[str, Any] | None = None, json: bool = False,
) -> pandas.DataFrame | list[dict]
```

Valid resources are exactly `diseases`, `drugs`, `tractability`,
`pharmacogenetics`, `expression`, `depmap`, and `interactions`. An invalid
resource raises `ValueError`. The normal Python result is a DataFrame; use
`json=True` for a list of JSON-compatible records. The Python API has no
`save` or `out` argument: write `df.to_csv(...)` or `df.to_json(...)` yourself
after checking the result. The CLI supplies `--out` and `--csv` equivalents.

## Resource choice and schemas

| Resource | Main flattened columns | Useful exact filters |
|---|---|---|
| `diseases` | `score`, `disease.id`, `disease.name`, `disease.description` | none documented |
| `drugs` | `drug.id`, `drug.name`, `drug.drugType`, `drug.maximumClinicalStage`, nested mechanism/indication fields | `drug.drugType`, `drug.maximumClinicalStage` |
| `tractability` | `modality`, `label`, `value` | none documented |
| `pharmacogenetics` | `variantId`, `genotypeId`, `genotype`, `drugs`, `pgxCategory`, `evidenceLevel`, `datasourceId`, consequence fields | `datasourceId`, `pgxCategory`, `evidenceLevel` |
| `expression` | `median`, `min`, `q1`, `q3`, `max`, `unit`, `datasourceId`, `datatypeId`, tissue/cell biosample fields | `tissueBiosample.biosampleId`, `datasourceId`, `datatypeId` |
| `depmap` | `tissueId`, `tissueName`, `cellLineName`, `mutation`, `expression`, `diseaseFromSource`, `depmapId`, `geneEffect` | `tissueId`, `diseaseFromSource` |
| `interactions` | `score`, `count`, `sourceDatabase`, `intA/intB`, target A/B and species fields | `sourceDatabase`, `targetB.id`, `targetB.approvedSymbol` |

Nested GraphQL fields are normalized with dot-separated names. Single-element
nested lists/dictionaries may be collapsed to a scalar or dictionary, so code
should inspect the actual dtype/value before assuming every nested field is a
list. Duplicate rows are removed after normalizing nested values.

Disease IDs are EFO-mapped associations, not a promise that every row is a
MONDO disease. Returned associations can be MONDO terms, HP phenotypes,
Orphanet terms, or EFO traits/measurements. `score` is the single aggregated
Open Targets target-disease association score in the 0–1 range, not a
per-source or per-data-type score. To retain only MONDO terms:

```python
df = gget.opentargets("ENSG00000169194", resource="diseases", limit=100)
mondo = df[df["disease.id"].astype(str).str.startswith("MONDO")]
```

## Limits and exact filters

`limit` narrows the final rows with `head(limit)`. Filters are applied
client-side after the API response and use exact equality against the returned
column name/value. Multiple dictionary entries are ANDed:

```python
interactions = gget.opentargets(
    "ENSG00000169194", resource="interactions", limit=20,
    filters={
        "sourceDatabase": "string",
        "targetB.approvedSymbol": "IL13RA1",
    },
)
```

A filter key absent from the returned columns raises `ValueError` and reports
available columns. Use returned spelling (`disease.id`, not `disease_id`) and
inspect one unfiltered row when designing a filter. The documented `limit` is
not compatible with `tractability` and `depmap`; avoid passing it for those
resources even though generic DataFrame post-processing may otherwise accept
it.

Expression is a special current resource. The old `target.expressions` tissue
z-score field is retired; gget queries `target.baselineExpression` and returns
per-biosample summary statistics. `limit=2` asks the API for a two-row page and
then keeps two rows. With no limit, gget asks for the API maximum of 3000 rows.
If upstream `count` exceeds 3000, gget warns that the result is truncated;
use `filters` such as `datasourceId="gtex"` or `datatypeId="bulk rna-seq"` and/or
an explicit limit. Bulk sources commonly fill `tissueBiosample.*`; single-cell
sources can fill both tissue and cell-type biosample fields.

## Reproducible recipes

```python
import gget

# Novice disease lookup with a bounded payload.
diseases = gget.opentargets("ENSG00000169194", resource="diseases", limit=10)
assert {"score", "disease.id"}.issubset(diseases.columns)
diseases.to_csv("il13_diseases.csv", index=False)

# Current baseline expression: narrow before broad exploration.
expr = gget.opentargets(
    "ENSG00000169194", resource="expression",
    filters={"datasourceId": "gtex", "datatypeId": "bulk rna-seq"},
    limit=100,
)

# DepMap and pharmacogenetic rows have distinct schemas.
depmap = gget.opentargets("ENSG00000169194", resource="depmap")
pgx = gget.opentargets(
    "ENSG00000169194", resource="pharmacogenetics",
    filters={"datasourceId": "clinpgx"},
)
```

For an Open Targets → G2P annotation handoff, preserve the Ensembl ID as the
canonical gene key. Disease rows provide associations, not a UniProt accession;
resolve the gene to a G2P UniProt pair explicitly and label that join as a
separate step. A minimal pattern is:

```python
ot = gget.opentargets("ENSG00000012048", resource="diseases", limit=20)
g2p_features = gget.g2p("BRCA1", uniprot_id="P38398", resource="features", residues=[185])
# Store the Open Targets disease rows and G2P rows separately; do not imply
# that a disease row supplies a residue-level causal annotation.
```

This synthetic case is useful because it tests both output schemas and the
portal-only boundary: G2P public rows do not include the portal's gnomAD,
ClinVar, or HGMD variant overlays.

## CLI and recovery

Representative CLI calls are:

```bash
gget opentargets ENSG00000169194 --resource diseases --limit 10 --out diseases.json
gget opentargets ENSG00000169194 --resource interactions \
  --filter sourceDatabase=string --filter targetB.approvedSymbol=IL13RA1 --csv
```

The CLI may expose `--or` for filter combination; Python's `filters` dictionary
is the documented AND form. Confirm installed CLI help if wrappers differ.

- **Bad ID/service error:** validate the `ENSG...` identifier with the
  identifier workflow, retry a small `diseases` query, and preserve the API
  error. A malformed target can surface as a service/normalization exception,
  not a meaningful empty biological result.
- **Invalid filter:** run once without filters, copy exact returned column
  names, then add one filter at a time. Nested keys use dot notation.
- **Empty rows:** the function returns an empty DataFrame/list and logs no data.
  Check target ID, resource spelling, and upstream availability.
- **Expression truncation:** heed the 3000-row warning; narrow by datasource or
  datatype before interpreting the sample as complete.
- **File output:** verify the written JSON/CSV and record resource, limit,
  filters, target ID, and retrieval date. Do not use disease row order as a
  stable identifier across platform releases.
