---
name: integration-tests
description: >-
  Given one or more user stories as free text, writes the committed system-test
  (integration) coverage that pis-gogrow's current develop actually supports end to
  end, defers whatever the story implies but the app can't do yet as an explicit
  comment (not silently skipped), and first checks for missing unit-test coverage
  (model/request/component specs) for the same story — listing gaps and waiting for
  a yes before writing any of them. TRIGGER: `/integration-tests <historia 1>` or
  `/integration-tests <historia 1> --- <historia 2> --- ...` for several at once.
  Typically run right after a user story's PR merges to pis-gogrow's develop.
---

Orchestrates three existing skills against real user-story text — it doesn't
reimplement their conventions, it decides *what* to write and *whether it's testable
yet*, then hands off:

- `rspec-developer` — model/request/mailer/helper specs (the unit-test gate).
- `vitest-rtl-developer` — component/hook specs (the unit-test gate, frontend side).
- `capybara-system-suite` — committed `spec/system/` browser specs (the integration
  tests this command exists to produce).

## Parsing multiple historias

The command receives one string. A single historia needs no delimiter — just the
pasted text. For more than one in the same invocation, expect them separated by a
line containing exactly `---`. If the text doesn't cleanly split that way (no
separator but clearly more than one story, or an ambiguous boundary), stop and ask
rather than guessing which sentence belongs to which story — silently merging two
stories into one produces wrong gap analysis for both.

## Before touching any historia: sync and check the known infra bug

1. Confirm `pis-gogrow` is on an up-to-date `develop` (`git status`, `git log -1`
   against `origin/develop`) — this command reasons about "what's implemented so
   far," which is meaningless against a stale or dirty checkout. If it's behind or
   dirty, say so and ask before proceeding rather than analyzing stale code.
2. Check `spec/support/authentication_helpers.rb`'s `System#sign_in`. If it still
   calls `page.driver.set_cookie(...)`, every system spec this command writes will
   fail immediately (`NoMethodError` — that method doesn't exist on the
   `:selenium, using: :headless_chrome` driver this project always uses for
   `type: :system`). Fix it per `capybara-system-suite`'s "Known bug" section before
   writing anything. This is a real fix to shared, committed code in the team's repo
   — flag it plainly in the final report as its own item, separate from the story's
   tests, since it's infra, not coverage.

## Per historia: figure out what's actually there before deciding what to write

Read first, don't pattern-match on the story's wording. For each historia:

1. Grep `config/routes.rb`, `app/controllers/`, `app/models/`, and
   `app/javascript/pages/`+`components/` for the feature area the story describes.
   Read the controller actions and the frontend page fully — an action can exist and
   still be an empty stub (`def edit; end`), a route can exist with no controller
   backing yet, a page can render but a button can do nothing. Treat "the story
   mentions X" and "X is actually wired up end to end" as different questions.
2. Cross-reference against `spec/` (and `app/javascript/**/*.test.tsx` if any exist)
   for what's already covered: missing spec files, generator `pending "add some
   examples"` stubs, a `describe` block with no real assertions for a path that
   *is* implemented.

## SimpleCov backs the gap list — treat it as installed

This project runs with SimpleCov (`rails-quality-metrics` has the gem/`spec_helper`
setup if it's ever missing — set it up from there rather than duplicating that
snippet here). Don't rely on reading code alone to guess at gaps when a precise
number is one command away:

1. Run the existing suite scoped to the files touched by the historia (or the whole
   thing if that's cheap enough): `bin/rspec <relevant spec files>`.
2. Read `coverage/coverage.json` for those same `app/` files — pull `missed_lines`
   from `covered_lines`/`total_lines` per file (same technique as
   `rails-quality-metrics`: parse the JSON, don't just eyeball the HTML) to get exact
   uncovered line numbers, not just "this file probably needs more tests."
3. Cross-reference those uncovered lines against what the historia actually touches.
   A file can be at 90% and still have the one branch this story cares about
   uncovered, or be at 60% entirely on code the story doesn't touch — the aggregate
   percentage isn't the gap list, the specific uncovered lines tied to this story are.

This is what turns "faltaría tests unitarios de X, Y y Z" into a list backed by real
uncovered lines instead of a guess from reading the file.

## Gate 1 — unit tests, ask before writing

Once the gap list for a historia is built, stop and ask in exactly this shape (one
line per historia, listing only what's actually missing and actually needed — a
model with no logic beyond associations already covered by an existing spec isn't a
gap):

> Faltaría realizar tests unitarios de X, Y y Z para la historia N. ¿Los realizo?

Wait for an explicit yes before writing any of them. A "no" for one historia doesn't
block proceeding to Gate 2 for that same historia — the unit-test gate and the
integration-test work are independent; a missing unit test is not a reason to skip
an integration test that's otherwise achievable (and vice versa: don't invent an
integration test just because unit tests got approved).

On yes: write them by invoking `rspec-developer` (backend) and/or
`vitest-rtl-developer` (frontend) — follow their conventions as written (fixtures vs
factories, shoulda-matchers, `userEvent` over `fireEvent`, etc.), don't re-derive
those rules here.

## Gate 2 — integration tests: write what's real, comment what isn't

For each user-facing flow the historia implies:

- **Fully wired (route + real controller action + real frontend page/handler)** →
  write it as a committed `spec/system/<flow>_spec.rb` per `capybara-system-suite`
  (role/label-based finders, no manual `sleep`, `sign_in`/`sign_out` from
  `AuthenticationHelpers::System`). Group scenarios from the same historia in one
  file when they're the same flow; separate files per distinct flow.
- **Partially wired or not wired (empty action, no route, no page yet)** → do not
  write a runnable spec for it and do not skip it silently. Add a plain comment (not
  a `pending`/`skip` block — this isn't a test RSpec should try to run) at the top of
  the relevant `spec/system/<flow>_spec.rb` — creating the file with just the comment
  if no scenario in that flow is testable yet — naming exactly what's missing:

  ```ruby
  # TODO(integración): falta implementar <lo que falta> antes de poder testear
  # <el escenario concreto de la historia>. Historia: "<historia, resumida>".
  ```

  If a later historia finishes what an earlier comment was waiting on, that's the
  cue to turn the comment into a real spec, not leave both.

## Verify before reporting done

Run what was written: `bin/rspec <files>` for backend/system specs,
`npx vitest run <files>` for frontend. A spec that fails because of a real app bug
(not a mistake in the spec itself) gets reported as a finding, same as
`rails-code-reviewer` would — this skill doesn't silently patch `app/` code to make
its own test pass.

## Final report, per historia

- Unit tests: written (list) / declined by the user / none needed.
- Integration tests: files written and what each covers.
- Deferred: each `TODO(integración)` comment added and why.
- Any infra fix applied (like the `sign_in` bug) or app bug found along the way,
  called out separately from the above.

## Write the report to a file, every run

Give the report above in chat as usual, but also write it to
`docs/reports/integration-tests/integration-tests-<dd-mm-aaaa>.md` **in this repo**
(`padre-testing-gogrow/`, never inside `pis-gogrow/`) — one file per command
invocation, even when it covers several historias (one section per historia inside
it), so there's a standing record of what a given run touched. `<dd-mm-aaaa>` is
today's date, e.g. `integration-tests-16-09-2026.md`; if the command runs more than
once on the same day, overwrite that day's file rather than numbering — it's a
per-day snapshot, not a log.

Beyond the per-historia content, this file is specifically for visibility into what
the run actually changed, so include a **files touched** section listing every file
created or modified during the run — spec files, `TODO(integración)` comments,
infra fixes (`spec/support/`, `Gemfile`, `spec/spec_helper.rb`, `.gitignore`,
etc.) — a plain list is enough, `git status --short` in `pis-gogrow/` is the source
of truth for it. Also name the branch/commit `pis-gogrow` was on for this run, since
that determines what "already implemented" meant at the time.
