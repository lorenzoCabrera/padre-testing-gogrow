---
name: integration-tests
description: >-
  Given one or more user stories as free text with their acceptance criteria (asks
  for both if a bare slug/ticket name comes in instead), writes the committed
  system-test (integration) coverage that pis-gogrow's current develop actually
  supports end to end, defers whatever the story implies but the app can't do yet
  as an explicit comment (not silently skipped), reports any real bug it finds
  along the way as its own dated defect file in this repo's docs/reports/defects/,
  and first checks for missing unit-test coverage (model/request/component specs)
  for the same story — listing gaps and waiting for a yes before writing any of
  them. TRIGGER: `/integration-tests <historia 1>` or `/integration-tests
  <historia 1> --- <historia 2> --- ...` for several at once. Typically run right
  after a user story's PR merges to pis-gogrow's develop.
---

Orchestrates three existing skills against real user-story text — it doesn't
reimplement their conventions, it decides *what* to write and *whether it's testable
yet*, then hands off:

- `rspec-developer` — model/request/mailer/helper specs (the unit-test gate).
- `vitest-rtl-developer` — component/hook specs (the unit-test gate, frontend side).
- `capybara-system-suite` — committed `spec/system/` browser specs (the integration
  tests this command exists to produce).

## What a historia looks like — ask if it doesn't

The command needs the actual free text of the user story **and** its acceptance
criteria, not a slug, branch name, or ticket title. If `ARGUMENTS` is short, reads
like a branch/ticket name (`realizar-pedido-empleado`, `IBP-006`, no sentence
structure), or has no visible acceptance-criteria list, stop and ask for both rather
than guessing scope from code, commit messages, or PR titles — a wrong guess produces
a wrong gap analysis silently, and by the time that surfaces the tests are already
written against the wrong thing:

> Pasame el texto de la historia de usuario y sus criterios de aceptación para poder
> analizarla.

Don't substitute a branch name, ticket ID, or your own summary of the code for this —
the acceptance criteria are what "fully wired" gets checked against in Gate 2, and
what "missing unit test" gets checked against in Gate 1.

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

## Turning each criterio into cases

Before deciding what's testable (Gate 2) or what's missing (Gate 1), expand each
acceptance criterion into concrete cases — one criterion often needs several, not
one spec each. For any criterion that describes accepting, creating, or updating
something with fields:

- The happy path, then check its *real* effect — the record exists with the right
  values, the redirect/props actually show it — not just a success message or a
  200.
- One negative case per field, one field at a time, everything else left valid:
  empty, whitespace-only, missing entirely, and for numeric fields zero and
  negative. Expect a clear error, nothing persisted, and no 500 — confirm via a
  fresh read/listing, not just the immediate response.
- Any limit the historia or the model actually defines (min, max, format,
  deadline): the allowed boundary value and one step past it (N and N+1). Don't
  invent a limit that isn't written down anywhere — if a case needs one and none
  exists, that's a question for the user (Gate 0, same as missing AC text), not a
  guess.

Test the criterion, not what the code currently happens to allow: if an AC says a
field is required and the server accepts it blank, that's a defect against the AC
— write it up (see "Bugs found along the way" below) even though the code treats
the field as optional today. Don't call a criterion satisfied because current
behavior is consistent; call it satisfied because it's what the historia actually
asked for.

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

## Transversal checks — apply when relevant, justify when not

These aren't in the historia's own acceptance criteria, but they apply to almost
anything with a role boundary or persisted state, so check for them on every
historia and write them into Gate 2 alongside the AC-literal specs. If one
genuinely doesn't apply (e.g. a pure read-only page with nothing role-scoped),
say so in the final report instead of silently skipping it — "difícil de probar"
is not the same as "no aplica".

- **Permisos y privacidad**: a role that shouldn't reach the feature (wrong role,
  no session) gets rejected server-side, not just hidden from the UI — a system
  spec asserting a redirect/403 on direct access, same pattern as the existing
  "rejects orders from a different active role" case in `orders_spec.rb`. For
  anything scoped to an individual rather than just a role — orders, payments,
  debt, personal data — also check peer-to-peer: two users of the *same* role,
  neither should reach the other's data through a direct record id/URL.
- **Persistencia y consistencia entre vistas**: data survives a reload and a
  sign-out/sign-in round trip. When the same operation is visible from more than
  one role's screen (an order a consumer places and a provider sees, a payment an
  employee makes and HR reconciles), the amount/status/identifier have to agree
  across both — don't only assert against the creator's own view.

## Verify before reporting done

Run what was written: `bin/rspec <files>` for backend/system specs,
`npx vitest run <files>` for frontend. A spec that fails because of a real app bug
(not a mistake in the spec itself) gets written up as a defect (see below), same as
`rails-code-reviewer` would flag it — this skill doesn't silently patch `app/` code
to make its own test pass.

## Bugs found along the way — report them, don't just mention them

Investigating "what's actually there" (Gate 2) and verifying what got written both
turn up real defects sometimes, not just gaps: a spec that fails against working
spec code because the app itself is wrong, a button with no handler, a page that's
live but unreachable from the app's own navigation, a criterion that's visually met
but not functionally. Any of these is a bug, not a "TODO(integración)" — those are
for work that isn't implemented *yet*; a bug is something implemented wrong or left
half-connected. Don't fold a bug into a `TODO(integración)` comment or bury it in
prose in the final report — write it up as its own file, one per defect, using
exactly this format:

```markdown
# Registro del defecto

**Título:**
[Descripción breve y específica del comportamiento incorrecto]

**Tipo:**
[Funcional / Documentación / Usabilidad / Seguridad / Otra categoría acordada]

**Historia o requisito relacionado:**
[Ítem del backlog o identificador RF/RNF relacionado]

**Criterio de aceptación afectado:**
[Condición esperada que no se está cumpliendo]

**Severidad:**
[Bloqueante / Alta / Media / Baja]

**Entorno o versión:**
[Ambiente y versión donde se observó]

**Precondiciones:**
[Datos o estado necesario antes de reproducir el defecto]

**Pasos para reproducir:**
1. [Primer paso]
2. [Segundo paso]
3. [Tercer paso]

**Resultado esperado:**
[Comportamiento correcto según el requisito o criterio de aceptación]

**Resultado obtenido:**
[Comportamiento real observado]

**Evidencia:**
[Adjuntar captura, video, registro o dato útil cuando corresponda]

**Ubicación o artefacto:**
[Pantalla, módulo, componente, documento o artefacto donde se detectó]
```

If "Criterio de aceptación afectado" doesn't map to the acceptance criteria of the
historia being analyzed right now (e.g. it belongs to an older, already-merged
story you tripped over along the way, like a page that's a dependency but not
what this run is testing), say so explicitly in that field instead of forcing a fit
— judgment call, not a guess. "Evidencia" is code references (`file:line`) when a
screenshot would need spinning up the dev server for no real gain over reading the
wiring — don't launch `bin/dev`/Docker just for a picture of a button doing nothing.

Write each defect to its own file:
`docs/reports/defects/DEFECT-<slug-corto>-<dd-mm-aaaa>.md` **in this repo**
(`padre-testing-gogrow/`, never inside `pis-gogrow/`), `<slug-corto>` a few
kebab-case words from the title. One file per defect, not one per run — if the
same defect resurfaces in a later run, update the existing file rather than
duplicating it.

## Before calling a historia done

Check this against the report you're about to write, same spirit as a DoD gate —
don't compile the final report until each of these is true:

- Every acceptance criterion has a result: a written spec, a `TODO(integración)`
  comment, or an explicit "no aplica" with why — none left with no mention at all.
- No essential case (a negative/boundary case from "Turning each criterio into
  cases", or a transversal check that applied) was silently dropped — a case you
  decided not to write gets a line saying so, not silence.
- Nothing was accepted as satisfying a criterion just because "that's what the
  code currently does," when the criterion asked for something else — see it as
  the defect it is instead.
- Every `TODO(integración)`/pending gap is named in the report, not folded into a
  passing summary — a pending case is not a passed case.
- Every bug found has its own file under `docs/reports/defects/`, linked from the
  final report, not just described in prose.

## Final report, per historia

- Unit tests: written (list) / declined by the user / none needed.
- Integration tests: files written and what each covers.
- Deferred: each `TODO(integración)` comment added and why.
- Any infra fix applied (like the `sign_in` bug), called out separately from the
  above.
- Bugs found: one line each, linking to the `docs/reports/defects/DEFECT-*.md`
  file written for it — not the full defect text inline here, that's what the
  file is for.

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
