# Multi-Brand Theme Architecture & Guidelines

## Overview
This repository supports multi-organization web development, allowing applications and tools to inherit distinct brand identities (such as **Columbia County School District** or **Georgia Southern University**) dynamically or per build.

## Core Rules for Multi-Branding

### 1. Brand Asset & Style Isolation
- The live dashboard (`client/index.html`) defines both brands inline in one `<style>` block — there is no `theme.css` per brand and no `src/brands/<organization-id>/` isolation in the running app. (That directory exists as unwired React scaffolding — see `CLAUDE.md` Architecture Quirks. Don't theme through it.)
- Never hardcode brand-specific colors (e.g. `#00025D` or `#001344`) outside the `:root[data-brand="..."]` blocks.
- Always consume colors and fonts via the CSS custom properties below.

### 2. Actual Brand Token Schema (as shipped in `client/index.html`)
Each brand block currently defines exactly these properties — nothing more:

```css
:root[data-brand="<brand-id>"] {
  --brand-id: "<brand-id>";
  --brand-name: "Full Organization Name";
  --brand-primary: rgb(...);
  --brand-secondary: rgb(...);
  --brand-accent: rgb(...);
  --brand-bg: #......;
  --brand-surface: #......;
  --brand-text-primary: #......;
  --brand-text-secondary: #......;
  --brand-border: #...... or rgba(...);
  --brand-font: 'FontName', fallback, sans-serif;
}
```

There is no `--brand-primary-hover`, `--brand-font-family`, `--brand-border-radius`, `--brand-header-bg`, or `--brand-header-text` — those were aspirational names from an earlier draft of this doc and don't exist in the code. If a new component genuinely needs a hover-state color or a header-specific override, add it to **both** `:root[data-brand="..."]` blocks in `index.html` using this same `--brand-*` naming convention, and update this table.

### 3. Pre-Configured Official Organizations

| Brand ID | Organization | Primary Navy / Blue | Secondary / Gold | Accents & Fonts |
| :--- | :--- | :--- | :--- | :--- |
| `columbia-county` | **Columbia County School District** *(ccboe.net)* | **Deep Navy** (`#00025D` / `rgb(0, 2, 93)`) | **Crimson Red** (`#D9232E`) | Bright Blue (`#0055A5`), Font: *Barlow* |
| `georgia-southern` | **Georgia Southern University** *(Official Brand Guidelines)* | **GS Navy** (`#001344` / PMS 282) | **Accessible Gold** (`#B9832D`), Logo Gold (`#9A8348`) | Athletic Grey (`#A5ACAF`), Sky Blue (`#68CAEB`), Fonts: *Merriweather / Barlow* |
| `default` | Generic Default | Slate (`#1E293B`) | Indigo (`#6366F1`) | Blue (`#3B82F6`), Font: *Inter* |

### 4. Brand Switcher (actual mechanism — vanilla JS, not React)
The live dashboard swaps brands by setting the `data-brand` attribute directly and updating a couple of header text nodes. This is the `switchTheme()` function already in `client/index.html`:

```js
function switchTheme(brandId) {
  document.documentElement.setAttribute('data-brand', brandId);
  if (brandId === 'georgia-southern') {
    document.getElementById('headerLogo').innerText = 'GS';
    document.getElementById('headerTitle').innerText = 'Georgia Southern Educational Analytics';
  } else {
    document.getElementById('headerLogo').innerText = 'GA';
    document.getElementById('headerTitle').innerText = 'Georgia Educational Analytics';
  }
}
```

A `<select class="theme-selector">` in the header calls this on change. Adding a third brand means: add a `:root[data-brand="new-id"]` block with the token schema above, add an `<option>`, and extend this `if/else` (or refactor it to a lookup table if a third brand is added — a 3-way if/else is the point to switch).

The `BrandProvider`/`useBrand` React context in `src/brands/` is unused scaffolding — do not wire new theming work through it unless the project has actually migrated to the React SPA (see `CLAUDE.md`).
