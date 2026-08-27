# Orange3 repo provenance

## Source snapshot

- Repository: `biolab/orange3`
- Public remote: `https://github.com/biolab/orange3.git`
- Branch: `master`
- Commit: `f7cee7e8337d166945d1a48322dd9b0b765ef432`
- Exact tag: none detected at the source commit
- Package distribution/version observed during inspection: `Orange3 3.41.0.dev0+f7cee7e`
- Public `Orange.__version__` observed during inspection: `3.41.0.dev`
- Working tree state during generation: dirty because the generated `skills/` tree and production log were present as untracked artifacts.

This skill should be refreshed if Orange3 APIs, widget signal contracts, Canvas discovery behavior, file-format behavior, or dependency constraints change significantly after the source commit above.

## Evidence paths distilled

### Package metadata and top-level docs

- `README.md`
- `README-dev.md`
- `CONTRIBUTING.md`
- `pyproject.toml`
- `setup.py`
- `setup.cfg`
- `requirements-core.txt`
- `requirements-gui.txt`
- `requirements-pyqt.txt`
- `requirements-sql.txt`
- `requirements-dev.txt`

### Data preparation evidence

- `doc/data-mining-library/source/index.rst`
- `doc/data-mining-library/source/tutorial/data.rst`
- `doc/data-mining-library/source/reference/data.rst`
- `doc/data-mining-library/source/reference/data.table.rst`
- `doc/data-mining-library/source/reference/data.domain.rst`
- `doc/data-mining-library/source/reference/data.variable.rst`
- `doc/data-mining-library/source/reference/data.io.rst`
- `doc/data-mining-library/source/reference/data.pandas.rst`
- `doc/data-mining-library/source/reference/data.sql.rst`
- `doc/data-mining-library/source/reference/preprocess.rst`
- `Orange/data/`
- `Orange/preprocess/`
- `Orange/data/sql/`
- `Orange/widgets/data/`
- `Orange/tests/test_io.py`
- `Orange/tests/test_tab_reader.py`
- `Orange/tests/test_txt_reader.py`
- `Orange/tests/test_table.py`
- `Orange/tests/test_domain.py`
- `Orange/tests/test_preprocess.py`
- `Orange/widgets/data/tests/`
- `Orange/tests/sql/`

### Supervised modeling evidence

- `doc/data-mining-library/source/tutorial/classification.rst`
- `doc/data-mining-library/source/tutorial/regression.rst`
- `doc/data-mining-library/source/reference/classification.rst`
- `doc/data-mining-library/source/reference/regression.rst`
- `doc/data-mining-library/source/reference/evaluation.rst`
- `doc/data-mining-library/source/reference/evaluation.testing.rst`
- `Orange/base.py`
- `Orange/classification/`
- `Orange/regression/`
- `Orange/modelling/`
- `Orange/evaluation/`
- `Orange/widgets/model/`
- `Orange/widgets/evaluate/`
- `Orange/tests/test_classification.py`
- `Orange/tests/test_regression.py`
- `Orange/tests/test_evaluation_testing.py`
- `Orange/widgets/model/tests/`
- `Orange/widgets/evaluate/tests/`

### Exploration and visualization evidence

- `doc/data-mining-library/source/reference/distance.rst`
- `doc/data-mining-library/source/reference/projection.rst`
- `doc/data-mining-library/source/reference/clustering.rst`
- `doc/data-mining-library/source/reference/clustering.hierarchical.rst`
- `doc/data-mining-library/source/reference/evaluation.clustering.rst`
- `Orange/distance/`
- `Orange/clustering/`
- `Orange/projection/`
- `Orange/statistics/`
- `Orange/misc/distmatrix.py`
- `Orange/widgets/visualize/`
- `Orange/widgets/unsupervised/`
- `Orange/tests/test_distances.py`
- `Orange/tests/test_clustering_kmeans.py`
- `Orange/tests/test_clustering_hierarchical.py`
- `Orange/tests/test_clustering_dbscan.py`
- `Orange/tests/test_clustering_louvain.py`
- `Orange/tests/test_pca.py`
- `Orange/tests/test_manifold.py`
- `Orange/widgets/visualize/tests/`
- `Orange/widgets/unsupervised/tests/`

### Widget development and Canvas evidence

- `doc/development/source/index.rst`
- `doc/development/source/tutorial.rst`
- `doc/development/source/tutorial-settings.rst`
- `doc/development/source/tutorial-channels.rst`
- `doc/development/source/tutorial-responsive-gui.rst`
- `doc/development/source/tutorial-utilities.rst`
- `doc/development/source/widget.rst`
- `doc/development/source/testing.rst`
- `doc/development/source/gui.rst`
- `doc/development/source/orange-demo/`
- `Orange/widgets/__init__.py`
- `Orange/widgets/widget.py`
- `Orange/widgets/gui.py`
- `Orange/widgets/settings.py`
- `Orange/widgets/tests/base.py`
- `Orange/widgets/tests/test_workflows.py`
- `Orange/widgets/tests/utils.py`
- `Orange/widgets/utils/`
- `Orange/widgets/report/`
- `Orange/canvas/`
- `Orange/canvas/workflows/`
- `Orange/canvas/tests/test_mainwindow.py`
- `Orange/widgets/tests/workflows/`
- `scripts/create_widget_catalog.py`

## Environment and backend baseline

- Inspection status: `ok`
- Minimum required backend for selected coverage: CPU + Qt/PyQt GUI support
- Accelerator backend required: none
- Optional service backend: PostgreSQL / SQL Server for SQL table/widget workflows, not prepared because it requires live services and credentials
- Confirmed installed imports during preparation: `Orange`, `Orange.data`, `Orange.classification`, `Orange.regression`, `Orange.evaluation`, `Orange.modelling`, `Orange.widgets`, `Orange.canvas`, `Orange.data.sql`, widget test/preview helpers
- Confirmed CLI smoke during preparation: `orange-canvas --help` under `QT_QPA_PLATFORM=offscreen`

Private environment paths and local command details are intentionally excluded from this public provenance. See construction artifacts under the review/test report directory if a future Creator needs the private setup log.
