---
name: regression-tests
description: >-
  Regression coverage for pis-gogrow historias that are already merged: same input
  as system-tests (blocks of IBP id + Como/quiero/para + criterios, with Pasos and a
  mandatory Esperado), but it starts from the specs that already exist. It maps
  every Paso, Esperado and criterio to the test that protects it, writes only what
  is missing (into that flow's own spec file), proves the whole set is stable
  against the calendar (every weekday, month end, year end) and against repeated
  runs, fixes flaky specs without touching app/, and writes a dated report that
  compares with the previous run of the same historias. TRIGGER:
  `/regression-tests <bloque> --- <bloque> ...`, "tests de regresión de IBP-…".
argument-hint: "IBP-003 Como… quiero… para… Criterios: 1… 2… | IBP-004 … | Pasos: … | Esperado: … --- (siguiente bloque)"
---

The goal is that every historia in the input ends up **protected by tests that
exist and are stable**. Writing new tests is the last resort, not the job.

Two files are the authority for everything not restated here. Read both in full
before starting:

- `.ai/skills/system-tests/SKILL.md`: input format and the template to show when
  the input is missing or malformed, user aliases (`E1`, `P1`, `A1`, `H1`), data
  rules, and how Pasos/Esperado turn into scenarios.
- `.ai/skills/integration-tests/SKILL.md`: sync and infra check, "what's actually
  there", turning criterios into cases, SimpleCov, Gate 1 (ask before writing unit
  tests), transversal checks, the defect file format, and the DoD checklist.

Only the differences are below.

## 1. Inventory first

Before writing anything, build a map for each block, row by row:

- every Paso and every "Repetir con X" variant,
- every sentence of the Esperado,
- every criterio of every historia in the block,

→ the existing spec(s) that protect it, as `file:line`. Search `spec/system/`,
`spec/requests/`, `spec/models/`, `spec/services/` and
`app/javascript/**/*.test.tsx`. A header comment naming the historia is a hint,
not proof: open the example and confirm it asserts the real effect (a persisted
record, another role's view), not just a flash message.

Mark each row:

- **Covered:** an example asserts it. Reference it and don't duplicate it.
- **Partial:** an example touches it but misses the negative/boundary case or the
  other role's view. Only the missing part gets written.
- **Not covered:** write it (step 2).
- **Not built:** the app doesn't do it yet. Write a `TODO(integración)` comment, as
  in integration-tests.

Also collect the `TODO(integración)` comments and `docs/reports/defects/` files
that already exist for these historias. They go into the report as-is, and you
don't open new defects for something already registered.

## 2. Fill only the gaps, in the flow's own file

- New examples go into the **existing spec file of that flow**: the one the
  inventory found for that screen or historia (for example
  `spec/system/consumer/consultar_menu_por_fecha_spec.rb`). Add the IBP id to that
  file's header comment if it isn't there. Create
  `spec/system/<carpeta-del-rol>/<flujo>_spec.rb` only when no file covers that
  flow yet.
- No separate `regresion/` folder. The report carries the command that runs the
  whole set.
- Same rules as system-tests for everything written: Pasos order, one scenario per
  "Repetir con X", real effects checked, negative/boundary cases, peer-to-peer
  permissions, consistency between views.
- Gate 1 (unit tests) still applies: list the missing ones and ask before writing.

## 3. Stability gate

A test only counts as "regression" if it passes this gate. The set is every spec
file from the inventory (existing and new), not just what this run wrote.

**Against the calendar.** Create this hook in a temp dir **outside both repos**
(`mktemp -d`; never commit it):

```ruby
# fake_today.rb
RSpec.configure do |c|
  c.include ActiveSupport::Testing::TimeHelpers
  c.around do |ex|
    travel_to Time.zone.parse("#{ENV.fetch('FAKE_DAY')} 12:00")
    ex.run
  ensure
    travel_back
  end
end
```

Then run the set once per date:

```bash
FAKE_DAY=<fecha> bin/rspec --require rails_helper --require <tmp>/fake_today.rb <spec files>
```

Use these dates: each day Monday to Sunday of next week, the last day of the
current month, and December 31. The hook travels without a block, so specs that
use `travel_to { }` themselves still work. It only moves the server's clock; the
browser keeps the real date. Say so in the report.

**Against chance.** Run the system specs of the set 5 times in a row with the
default random seed. Any failure means the test is flaky, even if it was 1 in 5.

**When something fails:**

- Find out first whether the test or the app is at fault. Read the failure and the
  screenshot, and reproduce it.
- **The test is at fault.** Fix it by touching only `spec/`. Typical fixes:
  - freeze the clock to a fixed weekday (`travel_to` a Monday at 10:00);
  - pick a date that can't collide with fixtures, for example
    `Date.current.next_week(:thursday)` after clearing that date;
  - disable animations with `execute_script` before clicking inside sheets or
    dialogs;
  - wait for the state with a Capybara matcher (`have_css("[aria-checked=true]")`)
    instead of assuming it.

  Don't change what the test asserts. If the spec belongs to a teammate (check
  `git log`/`git blame`), list it separately in the report: file, author, cause,
  fix.
- **The app is at fault.** That's a defect. Write the file (or update the existing
  one) and don't touch `app/`. Confirm it with a test, then **remove that test**
  before finishing. The suite this command leaves behind is green and has no
  `pending` examples for open defects. The defect file carries the reproduction
  steps, and the test gets written again once the team deals with it.
- After any fix, run the whole gate again for that file: all dates and the 5
  repeats.

## 4. Compare with the previous run

Look in `docs/reports/regression-tests/` for earlier reports that cover any of the
same IBP ids. For each row in the map, compare its status then and now:

- **Regressions:** it was covered and stable, and now it fails or lost its test.
  Put these first in the report.
- **Improvements:** a TODO or defect was resolved, or a gap got covered.
- **New:** rows that weren't in the previous run.

If there's no previous report, say "primera corrida" and skip the section.

## Report

Write the report to `docs/reports/regression-tests/regression-tests-<dd-mm-aaaa>.md`
**in this repo** (never inside `pis-gogrow/`). Overwrite it on same-day reruns. Give
the same content in chat. It has these sections:

1. **Header:** `pis-gogrow` branch and commit, and the run date.
2. **Per block, table** Paso → Esperado → test(s) `file:line` → estado.
3. **Per historia, table** criterio → test(s) → estado.
4. **Stability:** which dates were simulated, how many repeats, and the result per
   file. Note that the browser clock is not simulated.
5. **Flaky specs fixed:** file, author, cause, fix.
6. **Comparison with the previous run**, regressions first.
7. **Pending:** every `TODO(integración)` and defect, old and new, each linked.
8. **Rerun command:** the exact `bin/rspec` line with every file in the set, so
   anyone can rerun the regression.
9. **Files touched:** `git status --short` in `pis-gogrow/`, plus files in this
   repo.

Use these values in the estado column:

- ✅ estable
- 🔧 estabilizado en esta corrida
- ➕ test nuevo
- TODO
- 🐞 defecto (linked)

Never commit inside `pis-gogrow/`. That's a separate, manual step.
