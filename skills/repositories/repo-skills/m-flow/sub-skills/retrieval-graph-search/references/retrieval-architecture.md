# Retrieval architecture

M-flow retrieval is not only vector similarity over chunks. Search projects vector hits into a graph topology and ranks the complete memory units that the hits belong to. Use this page to explain why a result ranked highly, why a broad summary can be noisy, and which tuning knobs change retrieval behavior.

## Recall-mode routing

| Mode | Use for | Output tendency | Important caveat |
|---|---|---|---|
| `RecallMode.EPISODIC` | event/context recall over episodic memory | Episode summaries or Episode-Facet/Entity graph edges | Most tuning knobs in this sub-skill target this mode. |
| `RecallMode.TRIPLET_COMPLETION` | natural-language answers over graph context | LLM answer plus graph/context metadata | Depends on vector store, graph store, and LLM endpoint. |
| `RecallMode.CHUNKS_LEXICAL` | exact terms, keyword fallback, stopword-aware lookup | chunk/text matches | Less structural reasoning than graph modes. |
| `RecallMode.PROCEDURAL` | how-to, procedure, step retrieval | procedure context and steps | Route ingestion/learning of procedures elsewhere. |
| `RecallMode.CYPHER` | direct graph traversal by advanced users | raw graph query result | May be disabled with `ALLOW_CYPHER_QUERY=false`; user query must be Cypher. |

The simplified `query(question, mode="...")` maps mode strings to these recall modes: `episodic`, `triplet`, `chunks`, `procedural`, and `cypher`.

## Inverted-cone memory topology

Episodic retrieval uses an inverted cone of graph nodes:

| Level | Role in search | Typical precision |
|---|---|---|
| `FacetPoint` | atomic assertion or precise fact | very high; often the sharpest hit |
| `Entity` | named bridge across memories | high for name/entity queries |
| `Facet` | semantic aspect of an Episode | medium and interpretable |
| `Episode` | bounded semantic memory unit returned to users | broad; useful but prone to vague matches |

Search often enters through precise `FacetPoint`/`Entity`/`Facet` hits and lands on an `Episode`. This is why a result may be correct even when the query text does not look like the Episode summary: the best path can be through a specific fact or entity.

## Graph-routed Bundle Search

For `EPISODIC`, `episodic_bundle_search()` follows this sequence:

1. **Preprocess query.** Removes question-only words, optionally enables hybrid keyword+vector search for short, numeric, or mixed-language queries, and parses time expressions.
2. **Search vector collections.** Defaults include `Episode_summary`, `Facet_search_text`, `Facet_anchor_text`, `FacetPoint_search_text`, `Entity_name`, legacy `Concept_name`, and `RelationType_relationship_name`.
3. **Project a subgraph.** Vector hits become relevant node IDs, then the graph provider projects the surrounding episodic `MemorySpace` with node properties and edge properties `relationship_name` plus semantic `edge_text`.
4. **Map node and edge distances.** Node scores attach to graph nodes; `RelationType_relationship_name` hits attach semantic distances to edges using `edge_text`, `relationship_type`, or `relationship_name`.
5. **Build relationship index.** The index groups Episodes, Facets, FacetPoints, Entities, and edges such as `has_facet`, `has_point`, and `involves_entity`.
6. **Score Episode bundles.** Every possible path to an Episode is costed; the Episode score is the minimum path cost.
7. **Apply optional time bonus.** If the query contains a confident time expression, candidate pool width can expand and matched `mentioned_time`/`created_at` values can reduce scores.
8. **Assemble output.** Output edges/text are selected according to `display_mode` and per-Episode limits.

## Cost propagation

Bundle Search evaluates several paths to each Episode:

| Path name | Cost source | When it wins |
|---|---|---|
| `direct_episode` | `Episode_summary` vector distance plus `direct_episode_penalty` | broad question with no sharper supporting hit |
| `facet` | direct Facet hit → `has_facet` edge → Episode | query names an aspect/theme |
| `point` | FacetPoint hit → `has_point` edge → Facet → Episode | precise fact, number, assertion, or detailed condition |
| `entity` | Entity hit → `involves_entity` edge → Episode | cross-document or named-entity recall |
| `facet_entity` | Entity hit → Facet/Entity edge → Facet → Episode | entity is relevant through a specific facet |

Lower score is better. Costs combine:

- node vector distance from the best matching collection;
- semantic edge distance from `edge_text` when the edge was also hit by vector search;
- `edge_miss_cost` when an edge has no vector hit;
- `hop_cost` per traversal;
- `direct_episode_penalty` for broad Episode-summary hits.

The score is the **minimum** path cost, not an average. One strong chain of evidence is enough to retrieve an Episode even if other facets in the same Episode are unrelated.

## Why direct Episode hits are penalized

Episode summaries are deliberately broad. Without a direct-hit penalty, generic summary matches can dominate every query about the same topic and make broad questions look noisy. M-flow therefore adds `direct_episode_penalty` to direct Episode-summary paths so sharper paths from `FacetPoint`, `Facet`, or `Entity` can outrank a vague summary.

When a query is broad and no precise path exists, direct Episode hits can still win. When a query is precise and results look too broad, check whether the precise collections exist and whether `display_mode` is too summary-heavy.

## Adaptive scoring

Adaptive scoring estimates which vector collections are reliable for the current query:

- `top1_raw_distance / collection_baseline` estimates absolute match quality;
- the top-1/top-2 gap estimates discrimination;
- collections are grouped into node signals and edge signals;
- `w_node`, `w_edge`, and a semantic/structural fusion coefficient are clipped to bounded ranges.

Useful debug/tuning variables:

| Variable | Effect |
|---|---|
| `EPISODIC_ENABLE_ADAPTIVE` | enable/disable adaptive weights |
| `EPISODIC_ADAPTIVE_DEBUG` | emit debug logs for collection confidence |
| `EPISODIC_DEFAULT_BASELINE` | fallback baseline for unknown collections |
| `EPISODIC_LAMBDA_MIN`, `EPISODIC_LAMBDA_MAX` | bound semantic-vs-structural fusion |
| `EPISODIC_WEIGHT_CLIP_MIN`, `EPISODIC_WEIGHT_CLIP_MAX` | prevent all weight collapsing to one signal type |

Do not tune these first. Start with mode, `display_mode`, `top_k`, and collection coverage; use adaptive variables after you have evidence from verbose output or retrieval logs.

## Output display modes

| `display_mode` | What is returned | Use when |
|---|---|---|
| `summary` | synthetic Episode-summary edges/text | concise LLM context and broad recall |
| `detail` | Episode→Facet and Episode→Entity edges, no FacetPoints | need graph explanation, entities, or facet evidence |
| `highly_related_summary` | summary sections filtered by matched Facets | broad query returns too much unrelated summary text |

`max_facets_per_episode` and `max_points_per_facet` limit assembled detail. In default summary modes, `max_points_per_facet` may have little visible effect because FacetPoints are used for scoring but not shown.

## Evidence-backed checks

Use these checks when explaining a result:

```python
from m_flow.search.types import RecallMode
from m_flow.api.v1.search import search

results = await search(
    query_text="Which database migration missed the P99 target?",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    verbose=True,
    display_mode="detail",
    wide_search_top_k=150,
)
```

If detail mode shows only generic Episode/Facet edges, try adding precise collections explicitly:

```python
results = await search(
    query_text="P99 under 500ms",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    display_mode="highly_related_summary",
    collections=[
        "FacetPoint_search_text",
        "Facet_search_text",
        "Facet_anchor_text",
        "Entity_name",
        "RelationType_relationship_name",
    ],
)
```
