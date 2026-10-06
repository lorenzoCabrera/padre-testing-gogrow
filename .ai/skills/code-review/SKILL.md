---
name: code-review
description: >-
  Reviews a teammate's pis-gogrow PR — only the code that branch adds or changes
  against its base (develop by default), never the rest of the repo. One pass that
  combines rails-code-reviewer, rails-security-reviewer and rails-database-reviewer
  (adapted from the reference project's code-reviewer/security-reviewer/
  database-reviewer) plus correctness bugs, run on a throwaway worktree so the
  user's own pis-gogrow checkout is never touched. Writes one dated report in this
  repo. TRIGGER: `/code-review <rama>` or `/code-review <nº de PR>`, "revisá la
  rama X", "revisá el PR 85".
argument-hint: "<rama | nº de PR> [--base <rama>]"
---

Input: a branch name (`feature/IBP-060-cambio-validar-comprobante`) or a PR number
(`85`), optionally `--base <rama>`. No input → run `gh pr list` inside
`pis-gogrow/` and ask which one.

The checklists live in three other skills. **Read all three in full before
reviewing**; this file only replaces their *Scope* and *report* sections:

- `.ai/skills/rails-code-reviewer/SKILL.md`: conventions from `pis-gogrow/AGENTS.md`
  (read that file too, it's the authority).
- `.ai/skills/rails-security-reviewer/SKILL.md`: apply when the diff touches
  controllers, `skip_before_action :authenticate`, params, OmniAuth, sessions/cookies,
  secrets, or anything rendering user input.
- `.ai/skills/rails-database-reviewer/SKILL.md`: apply when the diff touches
  `db/migrate/`, `db/schema.rb`, models, scopes or queries.

## 1. Resolve the branch and base

Inside `pis-gogrow/`:

```bash
git fetch origin --prune
# PR number → its branch and base:
gh pr view <N> --json number,title,url,headRefName,baseRefName,author,body
```

- `HEAD_REF=origin/<rama>`, `BASE_REF=origin/<base>`; base is the PR's
  `baseRefName`, else `--base`, else `develop`.
- If the branch name was given, still run `gh pr view <rama> --json ...` to pick up
  the PR title/body/url (fine if there's no PR).
- Branch not on `origin` → stop and say so.

## 2. Scope: only what the branch adds

```bash
git diff --stat $BASE_REF...$HEAD_REF
git diff $BASE_REF...$HEAD_REF          # three dots = against the merge-base
git log --oneline $BASE_REF..$HEAD_REF
```

Three dots matter: if `develop` moved since the branch was cut, what `develop` added
afterwards is **not** part of this PR. Never review `git diff develop` (two dots) or
the user's working tree.

Rules for what counts:

- A finding must sit on a **line added or modified** by the diff, or be a bug the
  diff **introduces** elsewhere (e.g. it changes a method signature and an untouched
  caller now breaks, or it drops a validation something else relied on). Cite that
  caller and explain the link.
- Read unchanged code freely for context, but don't report problems that were
  already there. At most a one-line "fuera de alcance" list at the end of the report,
  only when one is serious.
- Skip generated churn when deciding *what* to review in detail (`db/schema.rb`
  version bump, `app/javascript/types/serializers/`, `app/javascript/routes/`,
  `package-lock.json`, `Gemfile.lock`), but the rails-code-reviewer rule still holds:
  a generated tree edited by hand is a finding. A lockfile change also means a new or
  bumped dependency, which belongs in the security pass.

## 3. Throwaway worktree for the tools

To read files at the branch's version and run linters/scanners without touching the
user's checkout (it may have uncommitted work):

```bash
WT=$(mktemp -d)
git worktree add --detach "$WT" $HEAD_REF
```

Then, in `$WT`, run only against changed files:

```bash
CHANGED_RB=$(git diff --name-only --diff-filter=AM $BASE_REF...$HEAD_REF -- '*.rb' '*.rake')
CHANGED_TS=$(git diff --name-only --diff-filter=AM $BASE_REF...$HEAD_REF -- '*.ts' '*.tsx')
bin/rubocop $CHANGED_RB
npx eslint $CHANGED_TS && npx prettier --check $CHANGED_TS
npx tsc --noEmit                   # whole project; report only errors in changed files
bin/brakeman --quiet --no-pager    # whole app; report only warnings in changed files
```

`$WT` has no `node_modules`; symlink `pis-gogrow/node_modules` into it if the JS
tools need it. If a tool can't run there (missing deps, DB), say so in the report and
keep going. Don't run the RSpec suite; a PR review isn't a CI run. Lint output
already caught by these tools gets one line per file, not one finding each.

Always clean up, even if the review stops early:

```bash
git worktree remove --force "$WT"
```

## 4. What to look for

In order of weight:

1. **Correctness.** Logic that doesn't do what the PR title/body/historia says,
   nil/empty cases, off-by-one on dates or quantities, timezone (`Time.current` vs
   `Time.now`/`Date.today`), wrong role allowed through, transactions that leave half
   a state on failure, N+1 in a new query, a flash/redirect that hides a failed save.
2. **Security and data:** from the other two skills, when they apply.
3. **Conventions:** rails-code-reviewer.
4. **Tests:** new behaviour (a new branch in a controller/model/service, a new page
   flow) without a spec that would fail if it broke. Name the missing case; don't
   write it. A spec in the diff that asserts only a flash message and not the
   persisted effect is a finding.
5. **PR hygiene:** title/body format from rails-code-reviewer; the PR also mixing
   unrelated changes.

Every finding needs a concrete failure: "with X, Y happens". If you can't say what
breaks, it's a 🟢 suggestion or nothing.

## 5. Report

One file: `docs/reports/code-review/PR_REVIEW_<rama-con-/-como-->_<YYYY-MM-DD>.md`
in **this** repo (never inside `pis-gogrow/`). Same-day rerun overwrites it. Written
in Spanish (it goes to teammates).

```markdown
# Revisión: <título del PR> (#<N>)

Rama `<rama>` → `<base>` · <n> commits · <archivos> archivos · merge-base `<sha corto>`
PR: <url> · Autor: <login>

## Resumen
<2-3 líneas: qué hace el PR y si está para mergear>

## 🔴 Crítico
- [ ] **[correctness] resumen corto** — `app/path/file.rb:42`
      Qué pasa, con qué entrada, por qué importa. Sugerencia de arreglo.

## 🟡 Advertencias
- [ ] ...

## 🟢 Sugerencias
- [ ] ...

## Herramientas
rubocop: ok / N ofensas en … · eslint: … · tsc: … · brakeman: … (o "no se pudo correr: …")

## Veredicto
Aprobar / Aprobar con cambios / Pedir cambios: <una línea de por qué>
```

Category tag is one of `correctness`, `security`, `database`, `conventions`, `tests`,
`pr`. Line numbers are the line in the **branch's version** of the file, so they
match GitHub's diff view. Empty section → omit it.

Finish in chat with the verdict, the count per severity and the report path.

## 6. Never

- Never checkout, commit, push or modify anything in `pis-gogrow/`; the worktree is
  the only thing created there, and it gets removed.
- Never post to GitHub (`gh pr review`, `gh pr comment`) unless the user asks for it
  explicitly after seeing the report. If they do, show the exact text first.
- No Fix mode here: the PR is someone else's. To fix things in your own branch, use
  the Fix mode of the three underlying skills.
