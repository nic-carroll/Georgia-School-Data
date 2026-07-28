# Multi-Brand Theme Architecture & Guidelines

## Overview
This repository supports multi-organization web development, allowing applications and tools to inherit distinct brand identities (such as **Columbia County School District** or **Georgia Southern University**) dynamically or per build.

## Core Rules for Multi-Branding

### 1. Brand Asset & Style Isolation
- Store each organization's assets and styles in dedicated subdirectories under `src/brands/<organization-id>/`.
- Never hardcode brand-specific colors (e.g. `#00025D` or `#001344`) directly into reusable UI components.
- Always consume colors, fonts, and brand attributes via standardized CSS custom properties (e.g. `var(--brand-primary)`).

### 2. Standard Brand Token Schema
Every brand definition file (`theme.css`) must expose these uniform custom properties:

```css
:root[data-brand="<brand-id>"] {
  /* Brand Identity & Colors */
  --brand-primary: rgb(...);
  --brand-primary-hover: rgb(...);
  --brand-secondary: rgb(...);
  --brand-accent: rgb(...);
  --brand-bg: hsl(...);
  --brand-surface: rgb(...);
  --brand-text-primary: rgb(...);
  --brand-text-secondary: hsl(...);
  
  /* Brand Typography & Badges */
  --brand-font-family: 'Merriweather', 'Barlow', 'Inter', sans-serif;
  --brand-border-radius: 6px;
  --brand-header-bg: var(--brand-primary);
  --brand-header-text: #ffffff;
}
```

### 3. Pre-Configured Official Organizations

| Brand ID | Organization | Primary Navy / Blue | Secondary / Gold | Accents & Fonts |
| :--- | :--- | :--- | :--- | :--- |
| `columbia-county` | **Columbia County School District** *(ccboe.net)* | **Deep Navy** (`#00025D` / `rgb(0, 2, 93)`) | **Crimson Red** (`#D9232E`) | Bright Blue (`#0055A5`), Font: *Barlow* |
| `georgia-southern` | **Georgia Southern University** *(Official Brand Guidelines)* | **GS Navy** (`#001344` / PMS 282) | **Accessible Gold** (`#B9832D`), Logo Gold (`#9A8348`) | Athletic Grey (`#A5ACAF`), Sky Blue (`#68CAEB`), Fonts: *Merriweather / Barlow* |
| `default` | Generic Default | Slate (`#1E293B`) | Indigo (`#6366F1`) | Blue (`#3B82F6`), Font: *Inter* |

### 4. Brand Switcher & Provider Usage (React)
Use the `BrandProvider` context wrapper in `src/App.jsx` to dynamically scope brand themes:
```jsx
import { BrandProvider, useBrand } from './brands/BrandProvider';

function App() {
  return (
    <BrandProvider defaultBrandId="georgia-southern">
      <Header />
      <MainContent />
    </BrandProvider>
  );
}
```
