# Experiment Workflows

## 1. FedAvg smoke run

Use this for the quickest end-to-end check after dataset validation.

```bash
python scripts/run_experiment.py \
  --repo-root <path-to-checkout> \
  --execute -- -data MNIST -m CNN -algo FedAvg -gr 1 -did 0 -dev cuda
```

Expected behavior:

- the server and clients are created
- evaluation prints an accuracy line
- the run saves a model checkpoint and an h5 result file

## 2. FedPAC smoke run

Use this when you need to confirm the cvxpy-backed algorithm path.

```bash
python scripts/run_experiment.py \
  --repo-root <path-to-checkout> \
  --execute -- -data MNIST -m CNN -algo FedPAC -gr 1 -did 0 -dev cuda
```

Expected behavior:

- `cvxpy` imports cleanly
- the quadratic head-aggregation path executes
- the run completes without a solver import error

## 3. Text-task smoke run

For AG News or Sogou News, set the vocabulary size to the dataset default and
choose a text model.

```bash
python scripts/run_experiment.py \
  --repo-root <path-to-checkout> \
  --execute -- -data AGNews -m fastText -algo FedAvg -vs 32000 -gr 1 -did 0 -dev cuda
```

## 4. Privacy and system-condition knobs

Enable DLG with the privacy flags and use the system-condition flags to model
client dropout, slow clients, and TTL pressure.

```bash
python scripts/run_experiment.py \
  --repo-root <path-to-checkout> \
  --execute -- -data MNIST -m CNN -algo FedAvg -gr 1 -dlg True -dlgg 1 -cdr 0.2 -tsr 0.2 -ssr 0.2 -tth 1000 -did 0 -dev cuda
```

## 5. Summarize the outputs

After the run finishes, point the summary helper at the generated h5 file or
at a `.out` log.

```bash
python scripts/summarize_results.py <path-to-checkout>/results/<file>.h5
```

or

```bash
python scripts/summarize_results.py <path-to-log>.out
```

## Order of operations

1. Validate the dataset tree.
2. Confirm the installation stack.
3. Launch the experiment.
4. Summarize the outputs.
5. Only then decide whether the run exposed a code-change or extension need.
