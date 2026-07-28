# Modern CSS & Multi-Brand System Guidelines

## Core Aesthetics
- **Rich Aesthetics**: Interfaces should look state-of-the-art, modern, and engaging with rich dark/light theme support, glassmorphism, dynamic gradients, and smooth hover micro-animations.
- **Multi-Brand Compatibility**: Components must inherit styling tokens from active brand themes (e.g., Columbia County School District, Georgia Southern University). See [`branding.md`](file:///Users/ncarroll/Claude/.claude/rules/frontend/branding.md) for organization details.

## Design Tokens & Brand Custom Properties
Component stylesheets must reference CSS variables injected by the active brand theme:

```css
:root {
  /* Brand Tokens (Overridden dynamically per active brand) */
  --brand-primary: hsl(215, 100%, 13%);
  --brand-primary-hover: hsl(215, 100%, 18%);
  --brand-secondary: hsl(43, 67%, 46%);
  --brand-accent: hsl(215, 100%, 25%);
  --brand-bg: hsl(210, 40%, 98%);
  --brand-surface: hsl(0, 0%, 100%);
  --brand-text-primary: hsl(222, 47%, 11%);
  --brand-text-secondary: hsl(215, 16%, 47%);
  
  /* Glassmorphism & UI Tokens */
  --border-subtle: rgba(0, 0, 0, 0.08);
  --backdrop-blur: blur(12px);
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-glow: 0 8px 32px 0 rgba(0, 0, 0, 0.12);
  
  /* Micro-Animations & Transitions */
  --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-smooth: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Interactive Styling & Component Patterns
- **Brand Buttons**:
  ```css
  .btn-brand {
    background-color: var(--brand-primary);
    color: #ffffff;
    border-radius: var(--radius-md);
    transition: background-color var(--transition-fast), transform var(--transition-fast);
  }
  .btn-brand:hover {
    background-color: var(--brand-primary-hover);
    transform: translateY(-2px);
  }
  ```
- **Brand Cards & Containers**:
  ```css
  .brand-card {
    background: var(--brand-surface);
    border: 1px solid var(--border-subtle);
    border-top: 4px solid var(--brand-secondary);
    border-radius: var(--radius-lg);
  }
  ```
