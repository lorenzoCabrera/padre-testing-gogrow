# CLAUDE.md

This is a personal **orchestrator repo**, not the project itself. It wraps
`pis-gogrow/` — an independent git repository (its own `.git`, its own
history, its own team) cloned inside this folder — and adds tooling that
belongs to me, not to the shared project: testing/quality-review skills, a
secrets-reading hook, and working notes.

## What's in here

```
padre-testing-gogrow/
├── .claude/
│   ├── settings.json      # PreToolUse hook: blocks Read/Grep on .env, master.key, etc.
│   ├── hooks/
│   └── skills/            # my 9 testing + quality-review skills, adapted for this stack
├── docs/
│   ├── architecture.md    # how the two repos relate, skill scoping
│   ├── runbook.md         # day-to-day commands
│   ├── glossary.md
│   └── reports/           # dated findings from the review skills — gitignored, ephemeral
├── scripts/setup.sh        # clones pis-gogrow if missing (idempotent)
└── pis-gogrow/             # the actual project — untracked here, see below
```

## First time here

```bash
scripts/setup.sh   # clones https://github.com/PIS-GoGrow/pis-gogrow.git into pis-gogrow/
cd pis-gogrow && bin/setup
```

## The project

`pis-gogrow/` is Rails 8.1 + Inertia.js + React 19 + TypeScript + PostgreSQL —
see `pis-gogrow/AGENTS.md` for its own conventions (that file is the
authority on how the app itself works; nothing here overrides it).
`pis-gogrow/.claude/skills/` already vendors the `inertia-rails/skills` set
(architecture, controllers, forms, pages, typescript, alba-inertia,
shadcn-inertia) — those are unrelated to the ones in this repo and load
scoped to that subdirectory. See `docs/architecture.md` for how skills from
both directories coexist in one Claude Code session opened at this root.

## Skills in `.claude/skills/`

Adapted from a Java/Spring/Angular reference project (`jp-photo-manager`) to
this stack. Nine skills across two groups:

**Testing:** `rspec-developer`, `vitest-rtl-developer`, `capybara-smoke-check`,
`capybara-system-suite`, `capybara-screenshot`

**Quality review:** `rails-code-reviewer`, `rails-security-reviewer`,
`rails-database-reviewer`, `rails-quality-metrics`

All four review/metrics skills write dated reports to `docs/reports/` **in
this repo**, never inside `pis-gogrow/` — that repo is shared with
teammates who don't use this setup. See `docs/runbook.md` for the concrete
commands and report locations.
