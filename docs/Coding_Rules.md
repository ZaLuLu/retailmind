# RetailMind — Coding Rules & Standards
**Last Updated:** 2026-05-19

> **Assistant Instruction:** Strictly follow these rules. Any code that deviates must be refactored before merging. When in doubt, match the existing patterns in the codebase rather than introducing new ones.

---

## General Principles

- **Clarity > Brevity** — Descriptive variable names. No single-letter variables outside loop counters.
- **Fail Fast** — Use Pydantic for strict type validation at the API boundary. Never trust raw input.
- **Async First** — All database and external API calls must be `async/await`. No blocking I/O.
- **No alert()** — Never use `window.alert()`, `window.confirm()`, or `window.prompt()`. Use the toast system.
- **No console.log in production** — Use structured logging on backend; remove debug logs before committing.

---

## Backend (Python / FastAPI)

### Typing
- Use type hints for all function signatures, including return types.
- Use `Optional[X]` for nullable fields, not `X | None` (keep consistent with existing code).

### Naming
- `snake_case` for variables, functions, module names.
- `PascalCase` for classes and Pydantic models.
- `UPPER_SNAKE_CASE` for constants.

### Models & Schemas
- SQLAlchemy models live in `app/models/db.py`. Inherit from `Base`.
- Pydantic schemas live in `app/schemas/`. One file per resource.
- Never return SQLAlchemy model objects directly from endpoints — always serialize to dict or Pydantic schema.
- Never expose `password_hash`, `refresh_token`, or internal IDs in API responses unless required.

### Error Handling
- Use `HTTPException` for all client-facing errors (4xx).
- Log internal errors with `logger.exception()` before raising HTTP 500.
- Never expose raw exception messages to the client in production.
- Pattern:
  ```python
  try:
      result = await some_service.do_thing(db, user_id)
  except Exception as e:
      logger.exception("Failed to do thing")
      raise HTTPException(status_code=500, detail="Failed to process request")
  ```

### Database
- All queries use SQLAlchemy async session (`AsyncSession`).
- Use `select()`, `func.*`, `and_()` from `sqlalchemy` — no raw SQL strings except for complex aggregations.
- Batch inserts in chunks of 100 (`db.add_all(batch); await db.commit()`).
- Always `await db.commit()` after writes. Never leave uncommitted transactions.

### Services
- Business logic lives in `app/services/`. API routes are thin — they validate input, call a service, return the result.
- Services receive `db: AsyncSession` and `user_id` as parameters. They do not access `request` objects.

---

## Frontend (React / Vanilla CSS)

### Component Pattern
- Functional components with hooks only. No class components.
- One component per file. File name matches component name (`PascalCase.jsx`).
- Props are destructured at the top of the function signature.

### State Management
- Local state with `useState`. Shared state lifted to `App.jsx` or passed via props.
- No Redux, Zustand, or Context API unless the state genuinely needs to be global (e.g., toast system, auth state).

### API Calls
- All API calls go through `src/services/api.js`. Never use raw `fetch()` in components.
- The `api.js` client handles auth headers, token refresh, and error normalization.
- Components receive data via props or call api methods in `useEffect`. No inline fetch calls.

### Error Handling
- Never use `alert()`. Use the toast system: `useToast()` hook.
- Show inline error messages for form validation errors (field-level, not toast).
- Show toast for async operation results (success/failure of API calls).
- Wrap the app in an `ErrorBoundary` component to catch render crashes.

### CSS
- Vanilla CSS only. No Tailwind, no CSS-in-JS, no styled-components.
- CSS Modules are acceptable for component-scoped styles.
- Follow the broadsheet design system:
  - Background: `#0D1B2A` (deep navy) or `#F5F0E8` (warm linen)
  - Accent: `#C9A84C` (gold)
  - Text: `#F5F0E8` on dark, `#0D1B2A` on light
  - Fonts: Playfair Display (headings), Source Serif 4 (body), JetBrains Mono (numbers/data)
  - No border-radius > 4px. No box-shadow (use solid offsets if depth needed).
  - All monetary values use JetBrains Mono.

### Accessibility
- All `<img>` elements must have `alt` text.
- All icon-only buttons must have `aria-label`.
- Interactive elements must be keyboard-navigable (Tab + Enter/Space).
- Color must not be the sole means of conveying information (add text label or icon).

---

## Design System Tokens

```css
/* Colors */
--navy:       #0D1B2A;
--gold:       #C9A84C;
--linen:      #F5F0E8;
--sand:       #EDE8D8;
--muted:      #8A9BB0;
--alert-red:  #D32F2F;
--success:    #2E7D32;

/* Typography */
--font-heading: 'Playfair Display', Georgia, serif;
--font-body:    'Source Serif 4', 'Times New Roman', serif;
--font-data:    'JetBrains Mono', 'Courier New', monospace;
--font-ui:      'Inter', Helvetica, sans-serif;

/* Spacing */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 40px;
```

---

## Git Workflow

- Commit messages follow Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Examples:
  - `feat: add demand forecasting endpoint`
  - `fix: token refresh race condition in api.js`
  - `refactor: remove legacy intelligence service`
- Keep commits focused. One logical change per commit.
- Never commit `.env` files, `node_modules/`, `__pycache__/`, or `*.pyc`.

---

## What NOT to Do

- ❌ Don't add new npm packages without checking if the functionality can be done in vanilla JS/CSS
- ❌ Don't add new Python packages without adding them to `requirements.txt`
- ❌ Don't write synchronous database calls
- ❌ Don't hardcode API URLs — use the `BASE_URL` constant in `api.js`
- ❌ Don't leave TODO comments in committed code — create a Feature_Log entry instead
- ❌ Don't duplicate logic between the frontend and backend — validation belongs on the backend, formatting belongs on the frontend
