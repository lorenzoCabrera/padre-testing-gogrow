---
name: rails-quality-metrics
description: >-
  Runs pis-gogrow's existing bin/ci pipeline (RuboCop, ESLint, Prettier, tsc, Typelizer
  freshness, bundler-audit, npm audit, Brakeman, RSpec) plus SimpleCov coverage, and
  reports trend against every previous report in this repo's
  docs/reports/quality-metrics/ — not just the last run. TRIGGER when asked for a
  quality/coverage report or how the metrics are trending. Deliberately minimal scope:
  no mutation testing, no accessibility auditing, no license/dead-code scanning — none
  of that tooling exists in pis-gogrow yet, and this skill doesn't invent it.
---

Adapted from `quality-metrics` in the reference project, cut down to what the user
explicitly chose: track what `bin/ci` already runs, add coverage, nothing more. The
reference project's broader sweep (mutation testing, Lighthouse a11y, license/SCA,
dead-code detection) has no equivalent tooling installed here — don't fabricate results
for checks that don't exist; if broader coverage is wanted later, that's a deliberate,
separate decision (new gems/packages), not something this skill should reach for.

## First-time setup — SimpleCov isn't installed yet

```ruby
# Gemfile, group :development, :test
gem "simplecov", require: false
```

`spec/spec_helper.rb` — **must be the first lines in the file**, before any other
`require` (SimpleCov misses coverage for anything already loaded before it starts):

```ruby
require "simplecov"
SimpleCov.start "rails"
```

## Running the sweep

```bash
cd pis-gogrow
bin/ci   # rubocop, eslint, prettier, tsc, typelizer freshness, bundler-audit, npm audit, brakeman, rspec
```

`bin/ci` already fails loudly per-step; this skill's job is to also capture the *numbers*
(offense counts, coverage %, pass/fail/pending counts, vulnerability counts) even when
everything passes, so drift is visible before it becomes a failure.

## Report

Write `padre-testing-gogrow/docs/reports/quality-metrics/QUALITY_METRICS_<date>.md`
with a `**Generated:** <ISO timestamp>` line at the top and one row per metric:

```markdown
**Generated:** 2026-09-11T18:30:00Z

| Metric | This run | Previous | Trend |
|---|---|---|---|
| RuboCop offenses | 0 | 0 | — |
| ESLint warnings | 0 | 0 | — |
| Brakeman warnings | 0 | 0 | — |
| bundler-audit vulnerabilities | 0 | 0 | — |
| npm audit vulnerabilities | 2 | 0 | ⚠ new |
| RSpec: passing / pending / failing | 41 / 6 / 0 | 38 / 9 / 0 | pending shrinking |
| Line coverage (SimpleCov) | 62% | 58% | ↑ |
```

**Compare against the whole history** in `docs/reports/quality-metrics/`, not just the
immediately preceding file — read every report in that directory and order them by each
file's own `**Generated:**` line, never by filename or file mtime (git doesn't preserve
original mtimes on clone/checkout, so mtime ordering silently lies). A single-run
regression can be noise; a metric worsening across the last several runs is the signal
worth calling out explicitly in the report's own summary line.

## What this skill never does

Never fixes anything itself, never adds a gem/package beyond SimpleCov without being
asked, never fabricates a mutation-testing/a11y/license number that no installed tool
actually produced. A regression found here becomes a `rails-code-reviewer` or
`rails-security-reviewer` finding (or a manual fix), not something this skill resolves
on its own.
