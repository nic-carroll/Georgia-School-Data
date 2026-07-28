# React Best Practices & Interactive UI Guidelines

## Component Architecture
- **Functional Components**: Use functional components with hooks. Avoid class components.
- **Single Responsibility**: Each component should handle one visual element or feature.
- **Component File Structure**:
  - Keep reusable UI widgets in `src/components/` (e.g. `Button.jsx`, `Modal.jsx`, `Navbar.jsx`).
  - Keep full view screens in `src/pages/` (e.g. `DashboardPage.jsx`, `LandingPage.jsx`).

## State Management
- **Local State**: Use `useState` for component-level interaction (toggle modals, active tab state, form inputs).
- **Server / Data State**: Use custom fetch hooks or React Query / SWR for handling remote backend data fetching, caching, loading indicators, and mutation side-effects.
- **Global State**: Use React Context or Zustand for cross-cutting state (user authentication context, theme mode, active notifications).

## Performance & UX Interactivity
- **Optimistic Updates**: Provide instantaneous visual UI responses on user actions while background requests resolve.
- **Loading & Skeleton States**: Never leave the user guessing; display pulse skeletons or spinners during async operations.
- **Error Boundaries**: Wrap major UI layouts with Error Boundaries to catch unexpected render errors without breaking the app.
