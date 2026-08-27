# Graph Time-Series Forecasting

## Core pattern

StellarGraph's time-series workflow combines a fixed graph adjacency with
sequence-valued node features. The public model class is `GCN_LSTM`.

Verified constructors:

```python
SlidingFeaturesNodeGenerator(G, window_size, batch_size=1)
GCN_LSTM(
    seq_len,
    adj,
    gc_layer_sizes,
    lstm_layer_sizes,
    gc_activations=None,
    generator=None,
    lstm_activations=None,
    bias=True,
    dropout=0.5,
    ...
)
```

## Sliding generator

`SlidingFeaturesNodeGenerator.flow(sequence_iloc_slice, target_distance=None)`
creates windows from a feature sequence. Use it to align input windows and
future targets.

Important terms:

- `window_size`: number of historical steps in each input window.
- `sequence_iloc_slice`: slice or range of time positions to generate.
- `target_distance`: how far after the window the target is selected; keep it
  consistent with forecast horizon.

## GCN_LSTM model

`GCN_LSTM` requires:

- `seq_len`: same historical length as the generator window;
- `adj`: fixed adjacency matrix for the graph;
- `gc_layer_sizes`: graph convolution output dimensions;
- `lstm_layer_sizes`: LSTM hidden dimensions;
- optional activation/dropout/initializer parameters.

## Practical workflow

1. Build a graph whose nodes represent sensors/locations/entities.
2. Prepare a numeric feature tensor indexed by time and node.
3. Create `SlidingFeaturesNodeGenerator(graph, window_size=seq_len, batch_size=...)`.
4. Get adjacency with `graph.to_adjacency_matrix().toarray()` or a normalized
   variant expected by the workflow.
5. Create `GCN_LSTM(seq_len=seq_len, adj=adj, gc_layer_sizes=[...], lstm_layer_sizes=[...])`.
6. Inspect generator batch shapes before compiling.

## Dataset helper note

`METR_LA` exposes helper methods `train_test_split`, `scale_data`, and
`sequence_data_preparation`, but using the real dataset requires download. For
shape debugging, prefer a synthetic time series.
