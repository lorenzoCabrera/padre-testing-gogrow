# Runbook

## Setup

```bash
scripts/setup.sh          # clone pis-gogrow (idempotent)
cd pis-gogrow && bin/setup
```

## Everyday commands (run inside `pis-gogrow/`)

```bash
bin/dev                                    # rails + vite
bin/rspec spec/requests/users_spec.rb:12   # one example; drop :12 for the file
bin/rubocop -a                             # autocorrect
npm run lint:fix / format:fix / check      # eslint / prettier / tsc
npm test                                   # vitest, once vitest-rtl-developer sets it up
bin/ci                                     # full local pipeline: rubocop, eslint, prettier,
                                            # tsc, typelizer freshness, bundler-audit, npm audit,
                                            # brakeman, full RSpec suite
```

## Review skills — trigger and output

| Skill | Trigger | Report lands at |
|---|---|---|
| `rails-code-reviewer` | after implementing a feature/fix in `pis-gogrow/` | `docs/reports/code-review/CODE_REVIEW_FINDINGS_<date>.md` |
| `rails-security-reviewer` | change touches auth, input, external calls, secrets | `docs/reports/security-review/SECURITY_REVIEW_FINDINGS_<date>.md` |
| `rails-database-reviewer` | new/changed migration, model, or scope | `docs/reports/database-review/DATABASE_REVIEW_FINDINGS_<date>.md` |
| `rails-quality-metrics` | asked for a quality/coverage trend report | `docs/reports/quality-metrics/QUALITY_METRICS_<date>.md` |

Each review skill has a **Fix mode**: point it at an existing dated report
and it works through unchecked findings one at a time, checking them off —
see each skill's own file for the exact loop. None of them ever commit;
committing inside `pis-gogrow/` is always a separate, explicit step.

## Testing skills

| Skill | Use for |
|---|---|
| `rspec-developer` | writing/filling in RSpec request, model, mailer specs |
| `vitest-rtl-developer` | React component tests (Vitest + Testing Library) |
| `capybara-smoke-check` | quick, throwaway browser check after building something |
| `capybara-system-suite` | committed regression specs under `spec/system/` |
| `capybara-screenshot` | "what does this page/dialog look like right now" |

## Where reports go and why

All four review/metrics skills write into **this repo's** `docs/reports/`,
never into `pis-gogrow/docs/`. That folder is shared with teammates who
don't use this personal setup — see `docs/architecture.md`.
