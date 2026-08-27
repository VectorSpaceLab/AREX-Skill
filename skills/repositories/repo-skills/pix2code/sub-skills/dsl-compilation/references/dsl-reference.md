# pix2code DSL Reference

## Purpose

Read this when validating or explaining pix2code `.gui` files before compilation.

## Grammar model

pix2code uses a small line-oriented DSL. The compiler treats `{` as an opening tag, `}` as a closing tag, and comma-separated tokens as leaf children. Spaces and newlines are removed during parsing.

A typical nested shape is:

```text
header {
  btn-active, btn-inactive
}
row {
  single {
    big-title, text, btn-green
  }
}
```

The root node is implicit and rendered with the platform's `body` mapping. Every opened container token becomes a child node. Leaf rows may contain one token or a comma-separated list.

## Shared structural concepts

| Concept | Meaning |
| --- | --- |
| opening tag | `{` starts children for the current token. |
| closing tag | `}` returns to the parent node. |
| content holder | Each platform mapping uses `{}` as the placeholder for rendered children. |
| random placeholders | Web text uses `[]`; Android and iOS text/ID mappings use `[TEXT]` and `[ID]`. |

## Platform vocabularies

### Web tokens

`header`, `btn-active`, `btn-inactive`, `row`, `single`, `double`, `quadruple`, `btn-green`, `btn-orange`, `btn-red`, `big-title`, `small-title`, `text`.

### Android tokens

`stack`, `row`, `label`, `btn`, `slider`, `check`, `radio`, `switch`, `footer`, `btn-home`, `btn-dashboard`, `btn-notifications`, `btn-search`.

### iOS tokens

`stack`, `row`, `img`, `label`, `switch`, `slider`, `btn-add`, `footer`, `btn-search`, `btn-contact`, `btn-download`, `btn-more`.

## Validation rules

- Token names are platform-specific. Do not compile web tokens such as `header` or `single` with the Android/iOS compilers.
- Braces must be balanced. The original compiler can move to a missing parent and fail later; the bundled compiler raises a direct nesting error.
- The compiler does not validate visual layout correctness. It only expands token templates.
- Placeholder text and generated IDs are not semantically meaningful. Use a deterministic seed when comparing outputs in tests.
