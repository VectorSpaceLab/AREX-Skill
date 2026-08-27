# Topic index

This README is a curated learning map, not an execution manual.

| README family | Typical ask | Route / local example |
| --- | --- | --- |
| The Python Language | syntax refresh, iteration, quick reference, generator/loop basics | use `python-basics.md`; provenance example: `basic_commands.py` |
| Useful Online Courses | beginner learning path | return course names only; no local code path |
| Data Science with Python | NumPy/scientific Python overviews, intro data-science reading | provide section-level links; no executable workflow |
| Pandas Library in Python | DataFrame basics, filtering, grouping, reshaping, cheatsheets | recommend pandas links and cheatsheets; no local code path |
| Machine Learning with Python | broad ML tutorials, algorithm overviews, comparisons | if runnable baseline is requested, route to `../../kaggle-linear-models/` |
| Scikit Learn | sklearn API, model-family tutorials, benchmark references | provenance example: `svm_sklearn.py`; runnable modeling -> `../../kaggle-linear-models/` |
| Linear Regression in Python | linear/OLS concepts, sklearn vs StatsModels | tutorial links only; for runnable linear-model workflows, route to `../../kaggle-linear-models/` |
| Logistic Regression in Python | logit, regularization, odds, sklearn vs StatsModels | provenance example: `Logistic Regression with StatsModels/logistic.py`; runnable regression -> `../../statsmodels-logit-workflow/` |
| k Nearest Neighbours in Python | nearest-neighbor tutorials and intuition | tutorial links only |
| Neural Networks in Python | from-scratch NN tutorials, library comparisons | tutorial links only |
| Decision Trees in Python | tree rules, split interpretation, tree tutorials | tutorial links only |
| Random Forest with Python | ensembles, feature importance, bagging | tutorial links only |
| Support Vector Machine in Python | SVM tutorials, kernels, sklearn SVC | provenance example: `svm_sklearn.py` |
| NLP / Text Mining in Python | tokenization, n-grams, text-processing tutorials | tutorial links only |
| Sentiment Analysis with Python | sentiment tutorials, Twitter sentiment reading | for Twitter ingestion or JSON streaming, route to `../../twitter-json-workflow/` |
| Pickle: convert a python object into a character stream | serialization and persistence tutorials | tutorial links only |
| AutoML | TPOT and auto-model-search reading | tutorial links only |
| Regex Related | regex cheat sheets and testers | route to external regex tools in the README; no local code path |
| Shell Scripting | subprocess, shell-in-Python, bash replacement reading | tutorial links only |
| Other good lists | secondary resource hubs and curated lists | use as fallback when a topic lacks a direct README family |

## Local-example routing
- `basic_commands.py` — modernize the four small Python basics patterns in `python-basics.md`.
- `Logistic Regression with StatsModels/logistic.py` — statsmodels logistic example; if the user wants a runnable regression flow, route to `../../statsmodels-logit-workflow/`.
- `Logistic-Regression/*.py` — legacy modeling examples; for an executable linear-model workflow, route to `../../kaggle-linear-models/`.
- `svm_sklearn.py` — simple SVM example used as a local illustration for scikit-learn questions.
- `Twitter-Data-Analysis/extract_twitter_data.py` — raw Twitter streaming provenance only; implementation asks belong in `../../twitter-json-workflow/`.
