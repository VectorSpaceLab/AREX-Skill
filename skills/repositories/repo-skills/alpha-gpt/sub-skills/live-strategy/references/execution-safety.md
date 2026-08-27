# AlphaGPT Execution Safety

This reference covers AlphaGPT's Solana/Jupiter transaction path. It is not authorization to trade. No live transaction should be sent unless the user explicitly authorizes the current wallet, funds, network, token addresses, and slippage limits.

## Required live environment variables

AlphaGPT's execution config loads environment variables, typically from the process environment or a `.env` file:

| Variable | Required for live trading | Purpose | Safety rule |
| --- | --- | --- | --- |
| `QUICKNODE_RPC_URL` | Yes | Solana RPC endpoint used by `AsyncClient` for balances, token accounts, transaction submission, and confirmation. | Check presence only in offline preflight; do not probe RPC without authorization. |
| `SOLANA_PRIVATE_KEY` | Yes | Payer keypair used to derive the wallet address and sign Jupiter swap transactions. The code accepts a base58 private key string or a JSON byte-array string. | Never print, log, paste into chat, commit, or parse it in generic validators. |

Jupiter quote/swap calls use the public Jupiter API base URL in the adapter; there is no separate API key in this code path.

Use [../scripts/alpha_gpt_trading_config_check.py](../scripts/alpha_gpt_trading_config_check.py) for offline env presence checks. It never prints secret values and never calls RPC or Jupiter.

## Wallet and funds checklist

Before any live run:

- Confirm the wallet address out of band without exposing the private key.
- Fund the wallet only with the SOL amount the user is prepared to risk, plus gas/priority-fee margin.
- Confirm token-account behavior for the intended tokens. A sell can only proceed when the wallet has a positive token balance for the mint.
- Understand that `ENTRY_AMOUNT_SOL` defaults to `2.0` SOL per entry and up to `MAX_OPEN_POSITIONS=3` positions can be open.
- Confirm that local `portfolio_state.json` matches the wallet after manual trades, partial sells, failed transactions, or restarts.

## Jupiter/Solana transaction flow

The execution layer is split across `JupiterAggregator`, `QuickNodeClient`, and `SolanaTrader`.

### Quote

`JupiterAggregator.get_quote(self, input_mint, output_mint, amount_integer, slippage_bps=None)` calls Jupiter `/quote` with:

- `inputMint`
- `outputMint`
- raw integer `amount`
- `slippageBps`
- `onlyDirectRoutes=false`
- `asLegacyTransaction=false`

It returns the JSON quote on HTTP 200 and returns `None` after logging an error for non-200 responses. A missing quote should block execution.

### Swap transaction

`JupiterAggregator.get_swap_tx(quote_response)` posts the quote to Jupiter `/swap` with:

- `quoteResponse`
- wallet public key from `ExecutionConfig.get_wallet_address()`
- `wrapAndUnwrapSol=true`
- automatic compute-unit price and priority-fee fields

It returns a base64 `swapTransaction` string or `None` on API failure.

### Sign

`JupiterAggregator.deserialize_and_sign(b64_tx_str)` decodes the base64 versioned transaction, signs the message with the payer keypair, and populates a signed `VersionedTransaction`. Any signing error must be treated as a hard stop because it may indicate a malformed key, corrupted transaction, or incompatible transaction format.

### Send and confirm

`QuickNodeClient.send_and_confirm(txn, max_retries=3)` submits the signed transaction with `send_transaction`, logs the signature, waits for confirmation, and returns the signature string on success. Exceptions return `None`.

### Buy path

`SolanaTrader.buy(self, token_address: str, amount_sol: float, slippage_bps=500)`:

1. Checks wallet SOL balance and requires `amount_sol + 0.02` SOL.
2. Converts SOL to lamports.
3. Gets a SOL-to-token Jupiter quote.
4. Requests the swap transaction.
5. Signs and sends the transaction.
6. Returns `True` on a confirmed signature and `False` otherwise.

The strategy runner separately uses a quote's `outAmount` plus mint decimals to estimate local `portfolio_state.json` entry size and price.

### Sell path

`SolanaTrader.sell(self, token_address: str, percentage=1.0, slippage_bps=500)`:

1. Derives the wallet public key.
2. Finds parsed token accounts for the mint using `TokenAccountOpts`.
3. Sums raw token balances.
4. Computes `sell_amount = int(raw_balance * percentage)`.
5. Blocks when raw balance or sell amount is zero.
6. Gets a token-to-SOL Jupiter quote.
7. Requests, signs, sends, and confirms the swap transaction.
8. Returns `True` only after a successful send/confirm path.

## Slippage behavior

- `ExecutionConfig.DEFAULT_SLIPPAGE_BPS` is `200` bps and is used when `JupiterAggregator.get_quote()` is called without an explicit value.
- `SolanaTrader.buy()` and `SolanaTrader.sell()` default to `slippage_bps=500`.
- `RiskEngine.check_safety()` probes a token-to-SOL sell-path quote with `slippage_bps=1000` and treats no quote as unsafe.

Higher slippage may increase fill probability but can materially worsen execution, especially for thin meme-token liquidity. Do not raise slippage to bypass quote failures without a user-approved risk decision.

## Unsafe native script warning

Do **not** use the native transaction adapter as a smoke test. Running the transaction adapter file directly executes an inline test that constructs `SolanaTrader` and calls `sell()` for a hardcoded token with `percentage=0.5`. If credentials and token balance are present, that path can attempt a real sell transaction.

Safe verification alternatives:

- Run the bundled offline checker.
- Inspect strategy JSON and portfolio JSON without importing transaction-capable modules.
- Use code review or mocks for quote/swap behavior unless the user explicitly authorizes live RPC/Jupiter calls.

## Authorization gate for any live command

Before starting the strategy runner or directly invoking trader methods, record the user's explicit authorization for:

- wallet identity,
- maximum SOL at risk,
- intended token universe,
- maximum slippage,
- RPC endpoint/network,
- whether Jupiter swaps may be sent,
- whether partial/complete sells may be sent,
- how to stop the loop.

If any item is missing, stay in offline validation and troubleshooting mode.
