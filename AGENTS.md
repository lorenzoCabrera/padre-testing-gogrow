# AGENTS.md

Instructions for any coding agent (DeepSeek, Codex, OpenCode, Cursor, Aider,
Cline, …). `CLAUDE.md` holds the same content for Claude Code; keep both in sync.

This is a personal **orchestrator repo**, not the project itself. It wraps
`pis-gogrow/`, an independent git repository cloned inside this folder with
its own `.git`, history and team. This repo adds tooling that belongs to me,
not to the shared project: testing/quality-review skills, a secrets rule, and
working notes.

## What's in here

```
padre-testing-gogrow/
├── AGENTS.md              # this file
├── CLAUDE.md              # same instructions, for Claude Code
├── opencode.json          # OpenCode: loads .ai/skills, defines /integration-tests, blocks secret reads
├── .ai/
│   └── skills/            # 10 testing + quality-review skills (plain Markdown, any agent can use them)
├── .claude/
│   ├── settings.json      # Claude-only hook that enforces the secrets rule below
│   ├── hooks/
│   └── skills -> ../.ai/skills   # symlink so Claude Code still finds the skills
├── docs/
│   ├── architecture.md    # how the two repos relate
│   ├── runbook.md         # day-to-day commands
│   ├── glossary.md
│   └── reports/           # dated findings written by the review skills
├── scripts/setup.sh       # clones pis-gogrow if missing (idempotent)
└── pis-gogrow/            # the actual project, untracked here
```

## First time here

```bash
scripts/setup.sh   # clones https://github.com/PIS-GoGrow/pis-gogrow.git into pis-gogrow/
cd pis-gogrow && bin/setup
```

## The project

`pis-gogrow/` is Rails 8.1 + Inertia.js + React 19 + TypeScript + PostgreSQL.
Its own conventions are in `pis-gogrow/AGENTS.md`. That file is the authority
on how the app works, and nothing here overrides it. Read it before you touch
app code.

## Hard rules

1. **Never read secrets.** Do not open, cat, grep or print `.env`,
   `config/master.key`, `config/credentials/*.key`, `config/credentials.yml.enc`,
   `*.pem`, `*.p12` or `id_rsa*`. If you need a value, ask me to paste it.
   (Claude Code enforces this with a hook. Other agents must follow it on their own.)
2. **Reports go in this repo.** Review, metrics, defect and integration-test
   reports go under `docs/reports/` here, never inside `pis-gogrow/`. That
   repo is shared with teammates who don't use this setup.
3. **Don't commit into `pis-gogrow/`** unless I ask. It has its own history
   and team.

## Skills

A skill is a Markdown playbook at `.ai/skills/<name>/SKILL.md`. Its
frontmatter `description` says when it applies. Your tool may not load skills
by itself. **When a task matches a skill below, read that SKILL.md in full
before starting and follow it step by step.** If two skills could apply, the
descriptions say which one wins.

| Skill | Use when |
|---|---|
| `rspec-developer` | Creating or fixing a spec under `pis-gogrow/spec/` (model, request, mailer, helper) |
| `vitest-rtl-developer` | Testing a React component or hook in isolation, or adding Vitest tooling |
| `capybara-smoke-check` | Proving a feature you just built works in a real browser, using a throwaway spec that gets deleted |
| `capybara-system-suite` | Adding or fixing committed browser specs under `spec/system/` |
| `capybara-screenshot` | "Show me what X looks like" or "take a screenshot of X" |
| `integration-tests` | Writing integration coverage for a user story after it merges to `develop` |
| `rails-code-reviewer` | Reviewing a diff or PR against the conventions in `pis-gogrow/AGENTS.md` |
| `rails-security-reviewer` | Reviewing changes to auth, OmniAuth, strong params, external input or secrets |
| `rails-database-reviewer` | Reviewing migrations, associations, validations, queries or indexes |
| `rails-quality-metrics` | Running a quality/coverage report and checking how it trends |

The four review/metrics skills write dated reports to `docs/reports/` in
this repo.

**Slash commands.** In OpenCode, `/integration-tests <historia>` works
(defined in `opencode.json`). Skills mention invocations like
`/integration-tests <historia>`. Without slash-command support, treat
"run integration-tests for <historia>" the same way: read
`.ai/skills/integration-tests/SKILL.md` and follow it with that story
text.

**Vendored skills.** `pis-gogrow/.claude/skills/` has a separate set from
upstream `inertia-rails/skills`: `inertia-rails-architecture`,
`-controllers`, `-forms`, `-pages`, `-setup`, `-testing`,
`-typescript`, `alba-inertia` and `shadcn-inertia`. When a skill here
mentions `pis-gogrow:<name>`, read
`pis-gogrow/.claude/skills/<name>/SKILL.md`.

**Tool names.** Skills sometimes say "Read", "Grep" or "Bash". Use whatever
file-read, search and shell tools your agent has.

See `docs/runbook.md` for the exact commands and report locations.
