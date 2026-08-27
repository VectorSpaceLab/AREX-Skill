# GUI DSL and styles

SketchCode predicts a compact GUI DSL, then compiles the token sequence into Bootstrap-based HTML through a style mapping.

## Compiler entry point

The compiler API is:

```python
Compiler(style).compile(generated_gui)
```

- `style` must be exactly `default`, `facebook`, or `airbnb`.
- `generated_gui` is a list of tokens. The historical sampler passes sequences shaped like `<START> ... <END>`.
- The compiler discards the first and last tokens with `generated_gui[1:-1]`, so include sentinels when calling the original compiler directly.
- On render failure, the compiler returns the literal string `HTML Parsing Error`.

## Basic grammar

The DSL uses braces for nested containers and commas for sibling separators. A typical sequence is:

```text
<START> header { btn-active , btn-inactive } row { single { big-title , text , btn-orange } } <END>
```

Practical rules:

- Container tokens are followed by `{ ... }`.
- Leaf tokens appear inside containers and should be separated by commas when matching the original compiler behavior.
- Balance every `{` with a matching `}`.
- Preserve known token names exactly; mappings are case-sensitive.
- If calling the original `Compiler.compile`, keep `<START>` and `<END>` around the sequence so the compiler's slice does not drop real content.

## Supported style names

| Style | Behavior |
| --- | --- |
| `default` | Historical Bootstrap-like styling with dark nav pills and neutral panels. |
| `facebook` | Same semantic DSL mapping with Facebook-like blue/gray color overrides. |
| `airbnb` | Same semantic DSL mapping with Airbnb-like teal/red color overrides. |

All three mappings support the same DSL token keys listed below. The alternate styles mainly change the CSS embedded in the `body` HTML mapping.

Unsupported style warning: the original `get_stylesheet(style)` only returns a path for `default`, `facebook`, and `airbnb`. Any other style can propagate `None` into file opening and fail with a bad path/`None` error rather than a friendly message. Validate style names before conversion.

## Token keys distilled from the mappings

| Token | Role |
| --- | --- |
| `body` | Root HTML document wrapper used internally by the compiler. |
| `header` | Header/nav container. |
| `btn-active` | Active nav pill. |
| `btn-inactive` | Inactive nav pill. |
| `row` | Bootstrap row container. |
| `single` | Full-width content column. |
| `double` | Half-width content column. |
| `quadruple` | Quarter-width content column. |
| `btn-green` | Green action button in default mapping. |
| `btn-orange` | Orange/warning action button; also the color-normalized comparison target in evaluation. |
| `btn-red` | Red/danger action button. |
| `big-title` | Large heading. |
| `small-title` | Small heading. |
| `text` | Paragraph placeholder. |

Unknown tokens render as `None` inside `Node.render`, which causes `Compiler.compile` to return `HTML Parsing Error`.

## Placeholder text behavior

The mappings contain `[]` placeholders. `Node.rendering_function` fills them using `SamplerUtils.get_random_text`:

- Button tokens receive random-looking text with default length `10`.
- Title tokens receive text of length `5` with no spaces.
- `text` receives lowercase paragraph-like text of length `56` with `7` spaces.

The bundled helper uses deterministic placeholder text instead of randomness so compiler checks are repeatable.

## Tiny compiler helper examples

From this sub-skill directory, compile a known-good sequence with the self-contained fallback:

```sh
python scripts/compile_tiny_dsl.py \
  --style default \
  --tokens '<START> header { btn-active , btn-inactive } row { single { big-title , text , btn-orange } } <END>'
```

Check another style:

```sh
python scripts/compile_tiny_dsl.py \
  --style airbnb \
  --tokens '<START> row { double { small-title , text } double { btn-red } } <END>'
```

Diagnose a likely parsing failure:

```sh
python scripts/compile_tiny_dsl.py \
  --style default \
  --tokens '<START> row { unknown-widget } <END>'
```

Expected result: the helper exits non-zero and prints an `HTML Parsing Error` message that identifies the unknown token.

## Common parsing mistakes

| Mistake | Why it fails | Fix |
| --- | --- | --- |
| Missing closing brace | The parse stack still has an open container at end of input. | Add a matching `}`. |
| Extra closing brace | The parser attempts to close past `body`. | Remove the extra `}` or add the missing opening container. |
| Bare `{` | The compiler expects a token key before an opening brace. | Use `row { ... }`, `header { ... }`, etc. |
| Unknown token | The style mapping has no HTML template for that token. | Replace it with one of the known tokens or retrain/change the model outside this sub-skill. |
| Missing commas between leaf siblings | The original compiler can remove spaces and concatenate adjacent leaf tokens into one unknown token. | Use commas, for example `big-title , text , btn-orange`. |
| Missing sentinels with original compiler | `generated_gui[1:-1]` drops the first and last tokens. | Wrap manual token lists with `<START>` and `<END>` before calling the original compiler. |
