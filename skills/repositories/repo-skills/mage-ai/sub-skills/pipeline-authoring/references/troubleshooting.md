# Pipeline authoring troubleshooting

## Common failures

### `NameError` for a decorator
- Keep the `if 'decorator' not in globals()` import pattern used by Mage templates.
- If you paste code into a standalone script, remember that the decorators are normally injected by Mage at runtime.

### Runtime variables are missing or have the wrong type
- Confirm the variable name is a valid Python identifier.
- Only primitive values and simple containers are supported.
- Read the values with `kwargs.get(...)` or the variable helper syntax, not by hard-coding them.

### SQL block fails with an identifier error
- Upstream data may not contain the expected column.
- Add a preprocessing transformer that ensures the column exists before the SQL block runs.

### A block freezes the browser or produces too much output
- The block may be writing too much sample data into the pipeline variables/output cache.
- Clear cached variables for the pipeline or reduce output size in the block.

### Dynamic blocks explode into too many child runs
- Set `DYNAMIC_BLOCKS_MAX_CHILD_BLOCKS` or the pipeline/block-level dynamic settings.
- Switch the overflow behavior from unlimited creation to `fail` or `limit` if the fan-out is unbounded.

### R code does not run
- R blocks are documented as Docker-only.
- Verify the project is running in a supported Docker-based Mage setup with the required R packages installed.

### The generated template looks wrong for the data source
- Use the connector-specific route for credential and `io_config` setup.
- This route only owns the block code itself, not the external connector configuration.
