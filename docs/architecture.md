# Architecture: parent/child repo

## Why two repos

`pis-gogrow` is a team project (its own `AGENTS.md`, its own GitHub Actions,
its own vendored Claude skills). This wrapper exists so my personal tooling
— extra skills, a secrets-reading hook, review-report history — never lands
in that shared repo's history or `.gitignore`. `pis-gogrow/` stays exactly
what the team pushes; nothing here modifies it except real commits I make
*inside* `pis-gogrow/`'s own git history, same as any other contributor.

`pis-gogrow/` is a plain clone, not a submodule: no commit-pinning, no
`.gitmodules`, no detached-HEAD surprises. `.gitignore` at this repo's root
just excludes the folder; git here never manages it at all.

## Skill scoping

Claude Code discovers `.claude/skills/` at multiple directory levels within
one project and scopes each by the subdirectory it's found in. Opening a
session at this repo's root (`padre-testing-gogrow/`) makes both sets
available at once:

- Skills in `padre-testing-gogrow/.ai/skills/*` (reached through the `.claude/skills` symlink) — the 14 adapted ones —
  load **unscoped** (this is the session root).
- Skills in `pis-gogrow/.claude/skills/*` — the vendored `inertia-rails`
  set — load **scoped** under a `pis-gogrow:` prefix (e.g.
  `pis-gogrow:inertia-rails-architecture`).

No naming collisions today (checked against the vendored set's 9 names).
If a future name collides, the directory-scoped one wins for files inside
that directory — see the project's own skill-selection notes if that comes
up.

## Division of responsibility

| Concern | Lives in |
|---|---|
| App code, its own tests, its own vendored Inertia skills | `pis-gogrow/` |
| `AGENTS.md` / architecture rules for the app itself | `pis-gogrow/AGENTS.md` — authoritative, not duplicated here |
| My testing/review skills | `padre-testing-gogrow/.ai/skills/` (symlinked as `.claude/skills/`) |
| Dated review findings, quality-metrics history | `padre-testing-gogrow/docs/reports/` (gitignored, personal) |
| Secrets-reading hook | `padre-testing-gogrow/.claude/settings.json` + `hooks/` |

## Stack the skills target

Rails 8.1, Inertia.js + React 19 + TypeScript, PostgreSQL, Vite. Backend
tests: RSpec (`rspec-rails`, `factory_bot_rails`, `faker`, `capybara` +
`selenium-webdriver` for system specs, `shoulda-matchers`). No Minitest
anywhere in the app. Frontend currently has no component-test tooling
(`vitest-rtl-developer` includes how to add it — Vitest + React Testing
Library, matching the existing Vite config).
