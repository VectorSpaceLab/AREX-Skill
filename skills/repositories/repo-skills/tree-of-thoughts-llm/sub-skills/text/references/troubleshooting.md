# Text Troubleshooting

## Coherency score parsing returns no matches

Likely cause: the judge output does not end with `Thus the coherency score
is N`.

Recovery:

- keep the judge prompt unchanged when possible;
- lower temperature if the judge becomes verbose or unstable;
- inspect a few raw judge completions before modifying the scorer.

## Vote parsing returns zeros

Likely cause: the model did not end with `The best choice is s` or used an
out-of-range index.

Recovery:

- keep the exact vote prompt wording;
- increase `n_evaluate_sample` for more stable majority votes;
- check that the candidate numbering in the prompt matches the candidate
  list order.

## Passage quality is weak

Likely cause: too few samples or a temperature that is too low or too high
for the current instruction.

Recovery:

- increase `n_generate_sample` first;
- keep `temperature=1.0` when replaying the paper command;
- use the naive CoT path to inspect whether the instruction itself is hard.

## API and auth failures

Use the shared root troubleshooting file for OpenAI credential, endpoint,
and network errors.
