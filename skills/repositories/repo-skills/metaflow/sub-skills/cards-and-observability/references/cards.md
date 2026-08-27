# Metaflow Cards

## Decorator surface

`@card` is a step decorator with defaults including:

- `type="default"`
- `id=None`
- `options={}`
- `scope="task"`
- `rank=None`
- `timeout=45`
- `save_errors=True`
- `customize=False`
- `refresh_interval=5`

Multiple cards can be placed on one step. Card `id` values must match the card ID pattern enforced by Metaflow; invalid IDs produce warnings and are not reliable keys for `current.card[ID]`.

## `current.card`

Inside a step decorated with an editable card, `current.card.append(...)` and `current.card.extend(...)` add user components. To disambiguate multiple cards, use `@card(id="name")` and `current.card["name"].append(...)`. `customize=True` selects the default editable card when there are multiple candidates.

Common components are imported from `metaflow.cards`, for example `Markdown`, `Artifact`, `Table`, `Image`, `JSON`, and event/timeline/value components.

## Card CLI

A flow script exposes:

- `card create`: create an HTML card.
- `card view`: view a card in a browser.
- `card get`: print/get HTML for a pathspec.
- `card list`: list cards.
- `card server`: run a local card viewer server.

Browser/server commands are local UI operations; avoid running them in headless automation unless explicitly requested.

## Custom cards

Custom cards subclass Metaflow card/component base classes and are usually packaged as extensions. Keep user-facing card components JSON-serializable and safe to render. If a card type cannot be found, verify extension loading and card type registration before editing flow logic.
