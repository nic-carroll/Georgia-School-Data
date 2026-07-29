# Modern CSS & Multi-Brand System Guidelines

## Reality Check — Read Before Adding "Rich Aesthetics"
`client/index.html` does **not** currently have hover states, CSS `transition`s, `backdrop-filter` glassmorphism, or a unified radius/shadow scale — `border-radius` alone is used inconsistently at `50%, 6px, 8px, 10px, 12px` across components, and `box-shadow` has three near-duplicate values. The "Core Aesthetics" goals below are the target, not the current state. If you're asked to "keep the design consistent," that means: match the *existing* ad-hoc values you find near the component you're editing, don't invent new tokens on the spot. If you're asked to actually improve consistency, the highest-leverage fix is introducing the token set in the next section for real (adding it to both `:root[data-brand=...]` blocks in `index.html`) and migrating existing components to reference it — that's a deliberate, scoped task, not something to do incidentally while fixing something else.

## Core Aesthetics (target, not yet fully implemented)
- **Rich Aesthetics**: Interfaces should look state-of-the-art, modern, and engaging with rich dark/light theme support, glassmorphism, dynamic gradients, and smooth hover micro-animations.
- **Multi-Brand Compatibility**: Components must inherit styling tokens from active brand themes (e.g., Columbia County School District, Georgia Southern University). See [`branding.md`](file:///Users/ncarroll/Claude/.claude/rules/frontend/branding.md) for organization details.

## Design Tokens — Actual, as shipped in `client/index.html`
This is the real token set defined in both `:root[data-brand="columbia-county"]` and `:root[data-brand="georgia-southern"]` blocks. Use exactly these names — do not introduce `--brand-primary-hover`, `--radius-md`, `--shadow-glow`, etc. without first adding them to both brand blocks (see `branding.md` §2):

```css
--brand-id            /* e.g. "columbia-county" — informational, not a style value */
--brand-name           /* full org name string */
--brand-primary        /* rgb(...) — header bg, primary accents */
--brand-secondary      /* rgb(...) — card top-border accents */
--brand-accent         /* rgb(...) — tertiary accent */
--brand-bg             /* page background */
--brand-surface        /* card/panel background, currently #FFFFFF for both brands */
--brand-text-primary
--brand-text-secondary
--brand-border
--brand-font           /* font-family stack */
```

## Real Component Classes
There's no `.btn-brand`/`.brand-card` convention in the code. The actual card-style components are `.viz-card`, `.selector-card`, and `.table-card`; layout containers are `.main-container`, `.controls-grid`, `.chart-container`; header pieces are `.app-header`, `.header-branding`, `.header-logo`, `.header-title`, `.theme-selector`. Match one of these existing patterns rather than introducing a new naming convention for a similar element.
