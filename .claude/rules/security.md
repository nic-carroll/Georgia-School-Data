# Security Best Practices

## Environment & Secret Management
- **Never hardcode secrets**: API keys, database credentials, JWT secrets, or private tokens must reside in `.env` files.
- **Git Safety**: Always include `.env` and `.env.local` in `.gitignore`. Provide a dummy `.env.example` with template keys.
- **Frontend Expose Limit**: Only expose client-safe variables prefixed appropriately (e.g., `VITE_API_URL`).

## Backend API Security
1. **CORS Policy**: Restrict origin access strictly to trusted client domains during production. ✅ Implemented — `server/src/index.js` scopes `cors()` to `process.env.CLIENT_ORIGIN` (default `http://localhost:5173`).
2. **Input Sanitization & Validation**: Validate all incoming `req.body`, `req.query`, and `req.params` (e.g., using `zod` or `joi`). ⏳ Not yet needed — current routes in `gosaRoutes.js` are read-only GETs against an in-memory dataset (no DB/shell interpolation). Add validation if a route ever accepts write input or feeds a query/shell command.
3. **Authentication**: Use secure HTTP-only, SameSite cookies or short-lived JWT tokens. ⏳ Not applicable yet — the API has no auth surface (all GOSA data is public). Apply this if an authenticated feature is ever added.
4. **Security Headers**: Enable security headers via `helmet` middleware in Express. ✅ Implemented — `app.use(helmet())` in `server/src/index.js`.
5. **Rate Limiting**: Protect authentication and heavy computation endpoints against brute force using rate-limiting middleware. ⏳ Not yet implemented — low priority while the server is local-only/dev; add `express-rate-limit` before any public deployment.

## Frontend Security
- Protect against Cross-Site Scripting (XSS) by avoiding direct `dangerouslySetInnerHTML` usage.
- Sanitize user input before displaying or sending to the backend.
- Ensure proper session lifecycle management (auto-logout on token expiration).
