# Query Troubleshooting

## Model or column not found during dry plan

Confirm the spelling and case against project context. A quoted identifier is
case-sensitive; an unquoted one can be resolved case-insensitively. Inspect the
model and rebuild the target after source changes.

## Planning error versus database error

Run the same SQL through `wren dry-plan`.

- If it fails, correct MDL, SQL, relationship, policy, or semantic naming.
- If it succeeds but execution fails, inspect the emitted dialect SQL and
  diagnose connector configuration, permission, database function support, or
  query cost.

## Connector import or authentication error

Install the exact datasource extra, use `wren docs connection-info` to confirm
fields, then inspect masked profile data. Do not replace a profile placeholder
with a secret in SQL or in `--connection-info`.

## Query is unexpectedly blocked

Check strict mode and denied-function policy. These controls deliberately reject
unmodeled tables or configured functions. Model the intended object or request a
policy change rather than trying to evade the guard.

## Cube query error

Use `wren cube describe` rather than raw SQL intuition. Validate complex cube
requests with `--sql-only`; a plan is safer than discovering a malformed metric
at a remote database.

## Correlated subquery failure

The semantic core has a known limitation with outer-column resolution in some
correlated subqueries. Rewrite toward a join, CTE, or non-correlated aggregation
when semantic planning cannot resolve the outer reference.
