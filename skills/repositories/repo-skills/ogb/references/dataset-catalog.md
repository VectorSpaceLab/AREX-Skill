# Dataset catalog

This catalog is distilled from the installed package metadata files and mirrors
what the loaders validate at runtime.

## Graph property prediction datasets (`ogbg-*`)

| Dataset | Task type | Metric | Notes |
| --- | --- | --- | --- |
| `ogbg-molbace` | binary classification | `rocauc` | molecular |
| `ogbg-molbbbp` | binary classification | `rocauc` | molecular |
| `ogbg-molclintox` | binary classification | `rocauc` | molecular |
| `ogbg-molmuv` | binary classification | `ap` | molecular |
| `ogbg-molpcba` | binary classification | `ap` | molecular |
| `ogbg-molsider` | binary classification | `rocauc` | molecular |
| `ogbg-moltox21` | binary classification | `rocauc` | molecular |
| `ogbg-moltoxcast` | binary classification | `rocauc` | molecular |
| `ogbg-molhiv` | binary classification | `rocauc` | molecular |
| `ogbg-molesol` | regression | `rmse` | molecular |
| `ogbg-molfreesolv` | regression | `rmse` | molecular |
| `ogbg-mollipo` | regression | `rmse` | molecular |
| `ogbg-molchembl` | binary classification | `rocauc` | molecular |
| `ogbg-ppa` | multiclass classification | `acc` | protein-protein association graph |
| `ogbg-code2` | subtoken prediction | `F1` | code-to-graph conversion workflow |

## Node property prediction datasets (`ogbn-*`)

| Dataset | Task type | Metric | Notes |
| --- | --- | --- | --- |
| `ogbn-proteins` | binary classification | `rocauc` | one graph |
| `ogbn-products` | multiclass classification | `acc` | one graph |
| `ogbn-arxiv` | multiclass classification | `acc` | citation graph |
| `ogbn-mag` | multiclass classification | `acc` | heterogeneous graph |
| `ogbn-papers100M` | multiclass classification | `acc` | binary/raw format |

## Link prediction datasets (`ogbl-*`)

| Dataset | Task type | Metric | Notes |
| --- | --- | --- | --- |
| `ogbl-ppa` | link prediction | `hits@100` | graph link prediction |
| `ogbl-collab` | link prediction | `hits@50` | graph link prediction |
| `ogbl-citation2` | link prediction | `mrr` | citation ranking |
| `ogbl-wikikg2` | KG completion | `mrr` | knowledge graph |
| `ogbl-ddi` | link prediction | `hits@20` | drug-drug interaction |
| `ogbl-biokg` | KG completion | `mrr` | heterogeneous KG |
| `ogbl-vessel` | link prediction | `rocauc` | external contribution / spatial sampling |

## OGB-LSC datasets

| Dataset | Evaluator | Notes |
| --- | --- | --- |
| `PCQM4M` | `PCQM4MEvaluator` | deprecated, use `PCQM4Mv2` |
| `PCQM4Mv2` | `PCQM4Mv2Evaluator` | molecular regression; submission files distinguish `test-dev` and `test-challenge` |
| `MAG240M` | `MAG240MEvaluator` | large heterogeneous node classification |
| `WikiKG90M` | `WikiKG90MEvaluator` | deprecated, use `WikiKG90Mv2` |
| `WikiKG90Mv2` | `WikiKG90Mv2Evaluator` | knowledge-graph completion with top-10 submission arrays |

## How to use this catalog

- Use the exact dataset names above when calling the loaders.
- Check the task type before choosing a metric-specific evaluator.
- Treat the deprecated LSC datasets as compatibility references, not preferred
  starting points for new work.
