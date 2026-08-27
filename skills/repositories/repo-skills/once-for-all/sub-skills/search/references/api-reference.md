# API Reference

## Purpose

Read this for the verified search APIs and the expected input/output shapes.

## Constructors

| API | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `AccuracyPredictor` | `AccuracyPredictor(pretrained=True, device='cuda:0')` | predictor instance | Use `pretrained=False` for offline smoke checks. |
| `FLOPsTable` | `FLOPsTable(pred_type='flops', device='cuda:0', multiplier=1.2, batch_size=64, load_efficiency_table=None)` | efficiency predictor | Can build or load a LUT. Building can be slow. |
| `LatencyTable` | `LatencyTable(device='note10', resolutions=(160, 176, 192, 208, 224))` | efficiency predictor | Loads public YAML lookup tables for the chosen device family. |
| `EvolutionFinder` | `EvolutionFinder(constraint_type, efficiency_constraint, efficiency_predictor, accuracy_predictor, **kwargs)` | search controller | Accepts `mutate_prob`, `population_size`, `max_time_budget`, `parent_ratio`, and `mutation_ratio` in `kwargs`. |

## Key methods

| Class | Method | Purpose |
| --- | --- | --- |
| `AccuracyPredictor` | `predict_accuracy(population)` | Predict accuracy for a list of sample dicts. |
| `FLOPsTable` | `predict_efficiency(sample)` | Return the predicted FLOPs for a sampled architecture. |
| `LatencyTable` | `predict_efficiency(spec)` | Return predicted latency for a spec dict with the expected `r`, `ks`, `e`, and `d` keys. |
| `EvolutionFinder` | `run_evolution_search(verbose=False)` | Run the regularized evolution loop and return `(best_valids, best_info)`. |
| `EvolutionFinder` | `set_efficiency_constraint(new_constraint)` | Update the current constraint without rebuilding the controller. |

## Input / output contracts

- `AccuracyPredictor.predict_accuracy` expects a list of architecture dicts.
- The tutorial search code uses sample dicts with keys like `ks`, `e`, `d`, and `r`.
- `best_info` is a tuple of `(predicted_accuracy, sample_dict, efficiency_value)`.
- `best_valids` is the history of the best accuracy seen at each generation.
