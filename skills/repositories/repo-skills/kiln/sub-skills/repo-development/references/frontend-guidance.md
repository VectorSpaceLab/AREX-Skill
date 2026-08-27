# Frontend guidance

Use this reference before changing Kiln's Svelte web UI, UI copy, component composition, layout, cards, tables, or web tests.

## Design goals

Kiln's UI is a modern B2B SaaS application for both technical and non-technical users. Maintain these qualities:

- Minimal, modern, typography-forward visual design.
- Consistent controls, spacing, colors, and interaction patterns across the app.
- Accessible language for inexperienced users without removing power for experienced users.
- Progressive disclosure for advanced options.
- Clear empty states that teach the concept and invite the next useful action.
- Apple-like restraint and polish rather than noisy or overly colorful UI.

## Copy and information architecture

- Use plain, descriptive text. Prefer everyday words unless technical precision matters.
- Keep primary UI strings short; put explanations in tooltips or supporting text when needed.
- Use `info_tooltip.svelte` or `info_description`-style patterns for concepts beginners need explained but experts should not repeatedly read.
- Hide optional expert controls in an advanced section, usually with `collapse.svelte`.
- Treat empty screens as onboarding opportunities: explain the benefit and provide a positive call to action.
- Avoid filler phrases and implementation jargon in user-visible strings.

## Preferred controls

Prefer existing app-specific controls before creating a new component or raw DaisyUI composition:

| Control | Use for |
| --- | --- |
| `app_page.svelte` | Standard page title, subtitle, and action button layout. |
| `property_list.svelte` | Name/value property grids with optional tooltips and links. |
| `form_element.svelte`, `form_container.svelte`, `form_list.svelte` | Forms with labels, validation, submit buttons, spinners, and errors. |
| `info_tooltip.svelte` | Inline help from an information icon without breaking layout flow. |
| `warning.svelte` | Informational, warning, success, or error callout boxes. |
| `intro.svelte` | Educational empty states with action buttons. |
| `dialog.svelte` | Modal dialog with close button, title, body, and actions. |
| `edit_dialog.svelte` | Editing name/description-like properties with save/cancel. |
| `collapse.svelte` | Advanced or optional sections. |
| `float.svelte` | Low-level floating positioning wrapper. Prefer higher-level menus when possible. |
| `floating_menu.svelte`, `table_action_menu.svelte` | Dropdown menus that work inside tables, dialogs, and scroll areas. Prefer these over DaisyUI dropdown content in constrained layouts. |

DaisyUI controls are allowed when no app-specific control fits. Examples include buttons, loading indicators, progress bars, badges, inputs, and standard layout helpers.

Before designing a new control, inspect similar existing usages in `app/web_ui/src/` and match their props, error handling, and visual hierarchy.

## Colors and typography

Use named DaisyUI/Tailwind classes from the established palette:

- `primary` for the main action. Usually only one `btn-primary` should appear on a screen.
- `btn-outline btn-primary` is acceptable for a set of peer primary choices.
- `success`, `error`, and `warning` only for meaningful status or feedback.
- `secondary` sparingly for extra emphasis.
- `text-base` for normal text and `text-gray-500` for secondary text.
- `bg-base-100` as the default inherited background; `bg-base-200` for subtle cards, blocks, or table headers when needed.

Do not set a custom font face. Use standard weights and sizes: `font-normal`, `font-medium`, `font-light`, occasional `font-bold`, and DaisyUI/Tailwind text sizes such as `text-xs`, `text-sm`, `text-lg`, `text-xl`, and `text-2xl`.

## Cards

Use this base card style:

```html
<div class="card card-bordered border-base-300 shadow-md">
  <!-- content -->
</div>
```

For clickable cards, add:

```text
hover:shadow-lg hover:border-primary/50 transition-all duration-200
```

Usually leave the background unset. Use `bg-base-200` only when a darker block is needed. Choose padding and sizing based on the surrounding layout rather than introducing a one-off card variant.

## Tables

Use the standard rounded bordered table wrapper:

```html
<div class="rounded-lg border">
  <table class="table">
    <thead>
      <tr>
        <th>Header 1</th>
        <th>Header 2</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Content 1</td>
        <td>Content 2</td>
      </tr>
    </tbody>
  </table>
</div>
```

For row actions inside tables, prefer `table_action_menu.svelte` or `floating_menu.svelte`. Raw DaisyUI dropdowns can break inside tables, dialogs, and scrollable containers.

## API client and state rules

- Use generated OpenAPI types from `api_schema.d.ts`; do not hand-write duplicate API response shapes when generated types are available.
- Keep API calls in stores or `$lib/...` helpers rather than embedding fetch logic deep in components.
- After backend route or Pydantic API changes, run the OpenAPI schema check and regenerate the client only when the schema change is intentional.
- For EventSource/SSE stores, close old sources before opening new ones and ignore stale callbacks after project switches.
- Keep component responsibilities small: components render state and invoke store/helper actions; stores own network state and side effects.
- Route detailed API/server behavior to `server-desktop-web-api`.

## Testing UI changes

Use the relevant subset while iterating, then broaden before handoff:

```bash
cd app/web_ui && npm run format_check
cd app/web_ui && npm run lint
cd app/web_ui && npm run check
cd app/web_ui && npm run test_run
cd app/web_ui && npm run build
```

Add or update tests when a UI change affects rendering decisions, validation, store behavior, EventSource handling, user actions, error states, or data transformation. Visual-only class changes may not need new tests, but they still need format/lint/type checks.

## Common pitfalls

- Too many primary buttons on one screen.
- One-off controls when an app-specific control already exists.
- Raw dropdowns inside tables/dialogs/scroll areas instead of floating menu components.
- User-facing copy that assumes deep ML/provider knowledge without tooltip support.
- Advanced options visible by default when they are optional and intimidating.
- Empty states that only say "No data" instead of explaining value and next steps.
- Duplicated API types or stale generated schema.
- Svelte 5-specific patterns in this Svelte 4 codebase.

## Evidence notes

Frontend guidance came from `AGENTS.md`, `.agents/frontend_design_guide.md`, `.agents/frontend_controls.md`, `.agents/card_style.md`, `.agents/tables_style.md`, and `app/web_ui/package.json`.
