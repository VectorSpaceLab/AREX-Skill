# Recording, Pretraining, Summaries, and Tracking

## TensorBoard summaries

Use `summarizer` in the agent spec:

```python
summarizer=dict(directory='summaries', summaries='all')
```

For short smoke tests, avoid summaries unless the task specifically checks TensorBoard output. Summary files are side effects and can grow quickly.

## Tracking tensors

Tensorforce agents expose `tracked_tensors()` for configured tracking values. Use this when the user needs internal diagnostics, but first build the minimal agent/environment smoke so failures are not confused with tracking setup.

## Recorder and pretraining

Recorder workflows store interaction traces and later feed them to `Agent.pretrain`. Keep the recorded data tied to the exact state/action specs and compatible agent architecture. If a user changes environment spaces or preprocessing, recorded traces may no longer load.

Safe workflow:

1. Define environment and agent specs.
2. Run a tiny online smoke.
3. Enable `recorder` only for the data collection phase.
4. Validate trace files exist and are small.
5. Call `agent.pretrain(...)` with matching specs and bounded steps.

Do not treat recorder/pretraining as a substitute for ordinary `observe`/`update` unless the task is explicitly offline/pretraining.
