# Game24 Troubleshooting

## Final answer scores `r=0`

Likely causes:

- the last line is not a valid equation;
- not all four input numbers are used exactly once;
- the arithmetic does not simplify to 24.

Recovery:

- keep the last line in the form `Answer: ... = 24`;
- check the intermediate states against the numbers left on the board;
- lower the temperature or increase `n_evaluate_sample` if the search gets
  stuck on noisy candidates.

## `value_prompt` output does not parse

Likely cause: the model drifted away from the expected `impossible`,
`likely`, `sure` labels.

Recovery:

- reuse the bundled prompt text instead of ad hoc prompt edits;
- reduce temperature;
- compare the raw `gpt` outputs before changing the search code.

## Search quality is poor

Likely cause: the evaluation count is too small or the frontier width is too
narrow.

Recovery:

- raise `--n_evaluate_sample` first;
- then consider a larger `--n_select_sample`;
- keep `method_select=greedy` while debugging so the frontier choice stays
  deterministic.

## API and auth failures

Use the shared root troubleshooting file for OpenAI credential, endpoint,
and network errors.
