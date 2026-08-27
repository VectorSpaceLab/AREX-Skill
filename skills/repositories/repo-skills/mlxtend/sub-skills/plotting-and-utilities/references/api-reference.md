# Plotting and Utilities API Reference

Use this reference for verified `mlxtend.plotting`, `mlxtend.data`, `mlxtend.file_io`, `mlxtend.text`, `mlxtend.math`, and `mlxtend.utils` call signatures and practical return notes. The root sub-skill router explains when to route here.

## Plotting helpers

All plotting helpers use Matplotlib objects. In headless environments set `MPLBACKEND=Agg` before importing `matplotlib.pyplot` or call `matplotlib.use("Agg")` first.

| API | Signature | Practical notes |
|---|---|---|
| `plot_decision_regions` | `plot_decision_regions(X, y, clf, feature_index=None, filler_feature_values=None, filler_feature_ranges=None, ax=None, X_highlight=None, zoom_factor=1.0, legend=1, hide_spines=True, markers='s^oxv<>', colors=..., scatter_kwargs=None, contourf_kwargs=None, scatter_highlight_kwargs=None, n_jobs=None)` | Needs a fitted classifier-like object with `predict`; `X` is numeric, `y` is 1D labels. For more than two features, choose two `feature_index` values and provide fillers for the remaining features. Returns/updates Matplotlib axes. |
| `plot_confusion_matrix` | `plot_confusion_matrix(conf_mat, hide_spines=False, hide_ticks=False, figsize=None, cmap=None, colorbar=False, show_absolute=True, show_normed=False, norm_colormap=None, class_names=None, figure=None, axis=None, fontcolor_threshold=0.5)` | Accepts a 2D confusion matrix. Returns `(fig, ax)` in typical use. Use `class_names` for labeled axes and close figures in batch jobs. |
| `plot_learning_curves` | `plot_learning_curves(X_train, y_train, X_test, y_test, clf, train_marker='o', test_marker='^', scoring='misclassification error', suppress_plot=False, print_model=True, title_fontsize=12, style='default', legend_loc='best')` | Fits/evaluates a classifier across training sizes; use small data in tests and route estimator choice to the estimator sub-skill. |
| `plot_sequential_feature_selection` | `plot_sequential_feature_selection(metric_dict, figsize=None, kind='std_dev', color='blue', bcolor='steelblue', marker='o', alpha=0.2, ylabel='Performance', confidence_interval=0.95)` | Expects `metric_dict` from `SequentialFeatureSelector.get_metric_dict()`. Route metric production to `feature-workflows`. |
| `plot_linear_regression` | `plot_linear_regression(X, y, model=LinearRegression(), corr_func='pearsonr', scattercolor='blue', fit_style='k--', legend=True, xlim='auto')` | Fits/plots a linear regression relationship; for estimator details use `estimators-and-ensembles`. |
| `heatmap` | `heatmap(matrix, hide_spines=False, hide_ticks=False, figsize=None, cmap=None, colorbar=True, row_names=None, column_names=None, column_name_rotation=45, cell_values=True, cell_fmt='.2f', cell_font_size=None, show_absolute=True, show_normed=False, figure=None, axis=None)` | Returns `(fig, ax)` in normal use. Accepts a 2D matrix plus optional row/column labels. |
| `checkerboard_plot` | `checkerboard_plot(ary, cell_colors=('white', 'black'), font_colors=('black', 'white'), fmt='%.1f', figsize=None, row_labels=None, col_labels=None, fontsize=None)` | Draws a table-like checkerboard/heatmap for a 2D array. |
| `category_scatter` | `category_scatter(x, y, label_col, data, markers='sxo^v', colors=('blue','green','red','purple','gray','cyan'), alpha=0.7, markersize=20.0, legend_loc='best')` | Expects columns in a pandas DataFrame or compatible mapping. |
| `scatterplotmatrix` | `scatterplotmatrix(X, fig_axes=None, names=None, figsize=(8, 8), alpha=1.0, **kwargs)` | Lower-triangular scatterplot matrix for numeric arrays/dataframes. |
| `scatter_hist` | `scatter_hist(x, y, xlabel=None, ylabel=None, figsize=(5, 5))` | Creates a scatter plot with marginal histograms. |
| `ecdf` | `ecdf(x, y_label='ECDF', x_label=None, ax=None, percentile=None, ecdf_color=None, ecdf_marker='o', percentile_color='black', percentile_linestyle='--')` | Plots an empirical cumulative distribution; accepts optional target percentile marker. |
| `plot_pca_correlation_graph` | `plot_pca_correlation_graph(X, variables_names, dimensions=(1, 2), figure_axis_size=6, X_pca=None, explained_variance=None)` | Computes/plots PCA correlation graph; variable name length must match features. |
| `enrichment_plot` | `enrichment_plot(df, colors='bgrkcy', markers=' ', linestyles='-', alpha=0.5, lw=2, where='post', grid=True, count_label='Count', xlim='auto', ylim='auto', invert_axes=False, legend_loc='best', ax=None)` | Uses a DataFrame of enrichment counts/curves. |
| `stacked_barplot` | `stacked_barplot(df, bar_width='auto', colors='bgrcky', labels='index', rotation=90, legend_loc='best')` | Plots stacked bars from a pandas DataFrame. |
| `remove_borders` | `remove_borders(axes, left=False, bottom=False, right=True, top=True)` | Removes selected Matplotlib spines from an `Axes`. |

## Data loaders and generators

| API | Signature | Returns and constraints |
|---|---|---|
| `iris_data` | `iris_data(version='uci')` | `(X, y)` arrays for iris. Tests cover valid `version` choices and invalid-choice errors. |
| `wine_data` | `wine_data()` | Wine feature matrix and labels. |
| `autompg_data` | `autompg_data()` | Auto MPG data. |
| `boston_housing_data` | `boston_housing_data()` | Boston Housing data packaged with mlxtend. |
| `mnist_data` | `mnist_data()` | 5000 packaged MNIST samples, `X` with 784 features and integer labels. Heavier than iris. |
| `loadlocal_mnist` | `loadlocal_mnist(images_path, labels_path)` | Reads local IDX/ubyte image and label files. Does not download them. |
| `three_blobs_data` | `three_blobs_data()` | Synthetic 2D blob data and labels. |
| `make_multiplexer_dataset` | `make_multiplexer_dataset(address_bits=2, sample_size=100, positive_class_ratio=0.5, shuffle=False, random_seed=None)` | Binary multiplexer dataset; use `random_seed` for reproducibility. |

## File IO helpers

| API | Signature | Practical notes |
|---|---|---|
| `find_files` | `find_files(substring, path, recursive=False, check_ext=None, ignore_invisible=True, ignore_substring=None)` | Returns file paths whose names contain `substring`. Use `check_ext='.csv'`-style extension filters. Invisible files are skipped by default. |
| `find_filegroups` | `find_filegroups(paths, substring='', extensions=None, validity_check=True, ignore_invisible=True, rstrip='', ignore_substring=None)` | Groups matching files across two or more directories by basename. Raises if group lengths differ and `validity_check=True`. |

## Text, math, and utility helpers

| API | Signature | Practical notes |
|---|---|---|
| `generalize_names` | `generalize_names(name, output_sep=' ', firstname_output_letters=1)` | Converts a personal name to a generalized form. |
| `generalize_names_duplcheck` | `generalize_names_duplcheck(df, col_name)` | Generalizes names in a dataframe and removes duplicates. |
| `tokenizer_words_and_emoticons` | `tokenizer_words_and_emoticons(text)` | Lowercase word/emoticon tokenizer. |
| `tokenizer_emoticons` | `tokenizer_emoticons(text)` | Extracts emoticons from text. |
| `factorial` | `factorial(n)` | Integer factorial helper. |
| `num_combinations` | `num_combinations(n, k, with_replacement=False)` | Count combinations with or without replacement. |
| `num_permutations` | `num_permutations(n, k, with_replacement=False)` | Count permutations with or without replacement. |
| `vectorspace_orthonormalization` | `vectorspace_orthonormalization(ary, eps=1e-13)` | Orthonormalizes column vectors. |
| `vectorspace_dimensionality` | `vectorspace_dimensionality(ary)` | Computes hyper-volume/dimensionality spanned by a vector set. |
| `Counter` | `Counter(stderr=False, start_newline=True, precision=0, name=None)` | Small progress counter for loops; avoid it when non-interactive logs should remain quiet. |
| `check_Xy` | `check_Xy(X, y, y_int=True)` | Checks supervised-learning input arrays. |
| `format_kwarg_dictionaries` | `format_kwarg_dictionaries(default_kwargs=None, user_kwargs=None, protected_keys=None)` | Merges default/user kwargs while preserving protected keys. |
| `assert_raises` | `assert_raises(exception_type, message, func, *args, **kwargs)` | Testing helper for expected exceptions; mainly useful when diagnosing failures. |
