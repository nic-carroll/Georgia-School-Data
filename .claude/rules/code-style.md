# Code Style & Naming Conventions

## General Principles
- Write clean, readable, self-documenting code.
- Prefer explicit names over cryptic abbreviations.
- Keep functions small, focused, and single-purpose.

## Naming Conventions
- **Components (React)**: `PascalCase` (e.g., `UserCard.jsx`, `NavigationHeader.jsx`).
- **Files & Utilities**: `camelCase` or `kebab-case` (e.g., `apiClient.js`, `format-date.js`).
- **Functions & Variables**: `camelCase` (e.g., `fetchUserData`, `isLoggedIn`).
- **Constants & Enums**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `MAX_RETRIES`).
- **CSS Classes**: `kebab-case` or BEM methodology (e.g., `.btn-primary`, `.card__header`).

## Module & Import Organization
Order imports predictably:
1. Standard library / React core modules
2. Third-party packages (e.g., `axios`, `express`, `lucide-react`)
3. Internal services & API clients
4. Reusable UI components & layouts
5. Helper utilities, constants, types
6. Stylesheets & assets

## Error Handling Standards
- Always use standard `try...catch` blocks for asynchronous operations.
- Return standardized error responses from backend API endpoints:
  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Human-readable description of error",
      "details": []
    }
  }
  ```
- On the frontend, gracefully handle loading and error states in UI components with fallback states or toast alerts instead of unhandled rejections.
