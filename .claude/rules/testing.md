# Testing Rules & Guidelines

## Overview
Comprehensive testing ensures reliability for interactive web apps across client interactions and API services.

**Current status: aspirational.** No test runner is installed in this repo yet (`client/package.json` and `server/package.json` have no `test` script, and no Vitest/Jest/Playwright config exists). Treat this file as the target setup to adopt when tests are introduced, not as a description of what's already running — don't assume `npm run test` works until a runner is actually wired in.

## Testing Layers

### 1. Frontend Unit & Component Tests
- **Tools**: Vitest / Jest + React Testing Library.
- **Focus**: Test component rendering, user actions (button clicks, form inputs, dynamic state changes), and accessibility attributes.
- **Rule**: Mock external network calls using API mocks (e.g. MSW) rather than making live network calls in unit tests.

### 2. Backend API Integration Tests
- **Tools**: Supertest + Vitest / Jest.
- **Focus**: Validate API endpoints, controller responses, middleware authentication, database transformations, and error handling.
- **Rule**: Ensure tests pass against clean test databases or memory stores.

### 3. End-to-End (E2E) Tests
- **Tools**: Playwright or Cypress.
- **Focus**: Core user journeys (User sign up/in, main dashboard interactions, data submission, responsive navigation).

## Test Command Conventions
- `npm run test`: Run unit and integration tests.
- `npm run test:watch`: Run tests in interactive watch mode during development.
- `npm run test:coverage`: Generate code coverage reports.
