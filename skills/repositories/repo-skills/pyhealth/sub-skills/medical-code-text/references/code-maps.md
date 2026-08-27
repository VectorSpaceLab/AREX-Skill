# Medical code maps

`pyhealth.medcode` exports `InnerMap` and `CrossMap` plus code-family classes
such as `ICD9CM`, `ICD10CM`, `ICD9PROC`, `ICD10PROC`, `CCSCM`, `CCSPROC`, `ATC`,
`NDC`, `RxNorm`, and `UMLS`.

Verified live signatures:

```text
InnerMap.load(vocabulary: str, refresh_cache: bool = False)
CrossMap.load(source_vocabulary: str, target_vocabulary: str,
              refresh_cache: bool = False)
```

Typical operations after loading an authorized mapping include `lookup(code,
field=...)`, `get_ancestors(code)`, and `map(code)` for a cross-map. Vocabulary
spelling and installed mapping assets matter. A code's meaning is coding-system
specific; never map an ICD-9 code as ICD-10 without an explicit source/target.

Mapping data may be cached or fetched depending on package state. For a safe
smoke, pass an explicitly available local vocabulary and a known code, or only
inspect class/API behavior. `refresh_cache=True` can trigger network/storage
side effects and must not be used implicitly in validation.

Code mapping can also be passed to a `BaseTask` as a field-to-pair dictionary;
the task then configures sequence processing for that field. Record whether
mapping occurs before or after cohort filtering and preserve unmapped-code
policy.
