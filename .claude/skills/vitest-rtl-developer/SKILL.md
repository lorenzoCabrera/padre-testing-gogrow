---
name: vitest-rtl-developer
description: >-
  React component/hook testing for pis-gogrow's frontend (React 19 + TypeScript + Vite +
  shadcn/ui) using Vitest + React Testing Library — the repo has none of this yet, only
  eslint/prettier/tsc. TRIGGER when creating or modifying a component/hook test, or when
  asked to add frontend test tooling. Scoped to leaf/presentational components and hooks
  only — full Inertia page flows (navigation, real form submission) belong to
  capybara-system-suite, not here.
---

Adapted from `cypress-unit-test-developer` in the reference project. This repo has **no
frontend test tooling at all** (checked `package.json`: only eslint, prettier, tsc) —
first use of this skill sets it up; skip setup if `vitest.config.ts` already exists.

## Scope — read this first

This skill covers **components and hooks in isolation** — rendering a component with
given props/context and asserting on what a user would see or do. It does **not** cover:

- Inertia response shape / props from the server → `pis-gogrow:inertia-rails-testing`
  (RSpec side) or `rspec-developer`.
- A full page navigating through real Inertia routes, submitting a real form to the
  Rails backend → `capybara-system-suite` / `capybara-smoke-check`.

If a component under test can't render without a live Inertia page visit (most files
under `app/javascript/pages/`), it's a Capybara concern, not a Vitest one. Vitest/RTL
targets `app/javascript/components/*`, `app/javascript/hooks/*`, and presentational
pieces that take props directly.

## First-time setup

```bash
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

`vitest.config.ts` at the repo root — deliberately separate from `vite.config.ts`,
which carries SSR/Inertia/Rails plugins that unit tests don't need:

```ts
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"
import path from "node:path"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./app/javascript") }, // mirrors tsconfig's "@/*"
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./app/javascript/test/setup.ts"],
  },
})
```

`app/javascript/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest"
```

`package.json` scripts:

```json
"test": "vitest run",
"test:watch": "vitest"
```

## Where tests live

Colocate `*.test.tsx` next to the file it tests (`hooks/use-clipboard.ts` →
`hooks/use-clipboard.test.ts`), not a parallel `__tests__/` tree — one file per unit,
found by proximity, matching how `spec/` mirrors `app/` on the Ruby side.

## Writing a test

Render, query by role/label like a user would, act with `userEvent` (not `fireEvent` —
`userEvent` sequences real browser events, `fireEvent` fires one DOM event and misses
what a real interaction implies):

```tsx
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

test("submits the typed value", async () => {
  const user = userEvent.setup()
  render(<SearchBox onSubmit={onSubmit} />)
  await user.type(screen.getByRole("textbox"), "query")
  await user.click(screen.getByRole("button", { name: /search/i }))
  expect(onSubmit).toHaveBeenCalledWith("query")
})
```

Assert on what's visible/accessible (role, label, text), not on internal state or
class names — a passing test that only checks a CSS class caught nothing real.

## Providers a component actually needs

Components use `react-i18next`'s `useTranslation` and `next-themes` for
light/dark — a component that calls either will throw without a wrapping provider.
Don't build a shared custom-render helper speculatively; the **first** test that hits
this should add a small `app/javascript/test/render.tsx` wrapping the providers it
needs, and later tests reuse it. Don't scaffold an empty one in advance.

## shadcn/ui (Radix) components

Radix primitives (dropdown, dialog, select) commonly need `ResizeObserver` and
`matchMedia` polyfilled under `jsdom` — if a test involving one of these hangs or
fails with a cryptic error about a missing global, that's very likely why; add the
polyfill to `test/setup.ts` rather than avoiding the component in tests. Not yet hit
in this repo (no tests exist yet) — flagging because it's a known class of issue with
this exact combination (Radix + jsdom), not something confirmed here.

## Mocking Inertia in a component test

If a leaf component imports something from `@inertiajs/react` (e.g. `router.visit` for
a button's side effect), mock the module rather than requiring a real Inertia page
context:

```ts
vi.mock("@inertiajs/react", async (importOriginal) => ({
  ...(await importOriginal()),
  router: { visit: vi.fn() },
}))
```
