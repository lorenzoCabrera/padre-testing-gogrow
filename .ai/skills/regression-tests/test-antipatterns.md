# Test anti-patterns seen in pis-gogrow

Each one has broken CI at least once. Shared by `regression-tests` (check the
set before the stability gate) and `code-review` (check specs the branch adds).
Grep for the pattern, then read the hit: a hit is a candidate, not a finding.

## 1. Moving or creating a schedule on a date a fixture may own

`spec/fixtures/schedules.yml` dates are ERB on the **real** date
(`Date.current + 3`, `- 5`, `+ 1`), and `schedules` has a unique index on
`menu_id + date`. A spec that puts `milanesa` (or another fixture menu) on a
date, fixed or relative, collides on the days the fixture lands there.

- Seen: Sundays (`next_occurring(:wednesday)` = today + 3), Fridays (next
  Monday = today + 3), 05-11 (`update_columns(date: 2026-10-31)` = today - 5).
- Same with `benefits.yml` (`benefits(:future)` due_date today + 10 crossing into
  next month).
- Grep: `rg -n 'Schedule\.create!|schedules\(:\w+\)\.update' spec/` and check the
  menu/date against the fixture file.
- Fix: clear the date first, keeping the records the spec itself moves:
  `Schedule.where(date: d).where.not(id: [...]).destroy_all` (team pattern, #58).
- **The calendar gate doesn't catch this one.** Fixtures load with the real
  clock before `fake_today.rb` travels, so they never move. Only reading the spec
  (or running on the unlucky real day) finds it.

## 2. `fill_in` with more than 30 characters on a React input

Capybara's Selenium driver types the first 4 keys, appends the middle by script
and types the last 3. A controlled React input never sees the scripted part;
depending on render timing the value ends up short (CI saved `"aaa"` of 501).
It also bypasses `maxLength`, so a boundary test proves nothing.

- Grep: `rg -n 'fill_in' spec/system | rg -v rapid` and look for long literals or
  `"x" * n`.
- Fix: `fill_options: { rapid: false }` on that call (7f5501bf).

## 3. Clicking inside a sheet, drawer or dialog while it animates

Radix sheets and vaul drawers move while sliding; on slower CI runners the click
lands on the wrong element or nowhere.

- Grep: system specs that open a sheet/dialog with no `without_animations` call.
- Fix: `without_animations` (`spec/support/animations.rb`) after `visit`.

## 4. Order that depends on `created_at` ties

Fixtures created in the same instant tie on `created_at`; `order(created_at:)`
then returns them in any order, and a spec asserting first/last flakes.

- Fix: give the records distinct timestamps, or assert without relying on order.

## 5. Assuming state instead of waiting for it

Reading an attribute right after a click (`find(...)[:"data-state"]`) races the
re-render.

- Fix: wait with a matcher (`have_css("[aria-checked=true]")`) before asserting.
