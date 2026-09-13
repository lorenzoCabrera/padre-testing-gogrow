---
name: rails-code-reviewer
description: >-
  Code review for pis-gogrow (Rails 8.1 + Inertia/React/TS) against this specific repo's
  own conventions from AGENTS.md — the Alba-Inertia serializer pattern, RuboCop-omakase
  overrides, generated-tree freshness (Typelizer/i18n/shadcn), declaration order. TRIGGER
  after implementing a feature/fix in pis-gogrow, or when asked to review a PR/diff. Also
  TRIGGERS to work through an existing dated CODE_REVIEW_FINDINGS report — see Fix mode.
---

Adapted from `code-reviewer` in the reference project. Same two-mode shape (Review then
Fix), scaled down to one report instead of a whole per-layer sweep system — this repo
doesn't have that project's PMD/JaCoCo/Stryker/knip machinery, and shouldn't invent it
(see `rails-quality-metrics` for the deliberately minimal quality-tooling story).

## Review mode

**Scope**: everything changed relative to the branch's base (`git diff
develop...HEAD -- .` inside `pis-gogrow/`, or `main...HEAD` if that's the actual base)
**plus** any uncommitted `git status --porcelain` on top — unlike a personal-orchestrator
branch that never commits, a normal `pis-gogrow` feature branch does commit, so both
halves matter; a review that only checks uncommitted changes misses everything already
committed to the branch.

**Write findings** to
`padre-testing-gogrow/docs/reports/code-review/CODE_REVIEW_FINDINGS_<YYYY-MM-DD>.md`
(this repo, never inside `pis-gogrow/` — see this repo's `docs/architecture.md`), one
checkbox per finding:

```markdown
- [ ] **[severity] short summary** — `app/path/to/file.rb:42`
      What's wrong and why it matters.
```

### What to check (repo-specific, from `pis-gogrow/AGENTS.md` — read that file's current
version before reviewing; don't rely on this list alone)

- **No `render inertia: { ... }`.** This app overrides `default_render` via
  `InertiaController`/`Alba::Inertia::Controller` — instance variables become props
  through a matching `*Serializer`. A `render inertia:` call is the generic pattern this
  repo explicitly does *not* use; flag it. Conversely, a page with suspiciously empty
  props is very likely a misnamed serializer (silently ignored, not an error) — check the
  serializer class name matches `{Namespace}::{Controller}{Action}Serializer` exactly.
- **Never `as_json`** in a serializer or controller — bypasses Typelizer's type
  generation silently.
- **Generated trees never hand-edited**: `app/javascript/types/serializers/`,
  `app/javascript/routes/`, `app/javascript/components/ui/` (shadcn),
  `app/javascript/locales/`. A diff touching these directly (not via
  `bin/rails typelizer:generate:refresh`, the shadcn CLI, or the i18n export) is a
  finding, not a legitimate change.
- **Translations start in `config/locales/en.yml`**, never a hardcoded string in a
  component — a new user-facing string added directly in JSX/TSX instead of an i18n key
  is a finding.
- **Forms use Inertia's `<Form>`/`useForm`**, never `react-hook-form` — and never manual
  `useMemo`/`useCallback` for the sake of it; the React Compiler (Babel, `vite.config.ts`)
  handles memoization, so hand-rolled memoization is very likely unnecessary noise unless
  the diff explains a specific case the compiler can't cover.
- **Declaration order**: models — constants → attr macros → enums → associations →
  validations → callbacks → scopes. Serializers — `typelize_from` → attributes → typed
  attributes → associations, each `typelize` directly above what it types. Components —
  imports (let `lint:fix` sort them) → props interface → default export.
- **RuboCop-omakase overrides actually enforced here** (not omakase defaults):
  indentation is `normal` (methods after `private` are *not* extra-indented),
  `Style/StringLiterals` (double quotes) covers every file. `frozen_string_literal` is
  cop-enforced — never hoist a string into a constant just to freeze it.
- **Comments are the exception**: one only for a non-obvious *why*/constraint/footgun,
  never narrating what the code says, never design rationale (that belongs in the commit
  message). A comment restating the method name below it is a finding.
- **No unrequested abstraction**: don't extract a constant unless it's genuinely reused
  across files or names an opaque value — passing an enum/inclusion list straight to the
  macro is preferred over a named constant used once.
- **PR conventions** (if reviewing a PR, not just a local diff): title `[ISSUE-ID] Short
  description` (real ticket key, or no brackets at all — never a placeholder); body is
  exactly `### Summary` (2-3 sentences) then `### Changes` (one bullet per change); no
  filler adjectives, one line per paragraph.

## Fix mode

Ask which report (default: the most recent in
`docs/reports/code-review/`), then which findings — work through unchecked ones one at a
time: fix it in `pis-gogrow/`, verify (rerun the relevant check — `bin/rubocop`,
`npm run lint`, `npm run check`, or the specific spec), then check the box and append
either `**Fixed:**` or `**Evaluated, no change made:**` with why. Never commits inside
`pis-gogrow/` — that's a separate, explicit step the human takes.
