---
name: rails-database-reviewer
description: >-
  Database review for pis-gogrow — PostgreSQL via Rails migrations (db/migrate,
  db/schema.rb), ActiveRecord associations, and index coverage. TRIGGER when adding or
  reviewing a migration, a model association/validation, or a query — including
  checking whether a new query actually uses the indexes that exist. Also TRIGGERS to
  work through an existing dated DATABASE_REVIEW_FINDINGS report — see Fix mode.
---

Adapted from `database-reviewer` in the reference project — same core checks
(normalization, index coverage, migration hygiene), scoped to plain ActiveRecord/Postgres
since there's no second datastore mirroring anything here (unlike the reference
project's Mongo/Redis mirrors).

## Review mode

Scope and report location: same as `rails-code-reviewer` — diff against branch base plus
uncommitted changes, findings at
`padre-testing-gogrow/docs/reports/database-review/DATABASE_REVIEW_FINDINGS_<date>.md`.

### Migrations

- **Never edit an already-applied migration.** A schema fix is always a new migration
  forward (`bin/rails g migration ...`), never an edit to one already run — this repo's
  own history already does this correctly (e.g. `remove_redundant_fields_from_providers`
  and `add_user_ref_to_consumers` as separate forward migrations fixing earlier ones,
  not edits to `create_providers`/`create_consumers`).
- `db/schema.rb` is generated from migrations, never hand-edited directly — a diff
  touching `schema.rb` without a matching new file in `db/migrate/` is a finding.
- `solid_queue`/`solid_cache`/`solid_cable` migrations live in the same primary database
  and same `schema.rb` — when reviewing schema diffs, separate "this app's own domain
  tables changed" from "a Rails/gem-owned table changed," don't flag the latter as an
  app design issue.

### Indexes

- **Every foreign key needs an explicit index** — Postgres doesn't create one
  automatically for a `belongs_to`/`references` column. `accounts` already does this
  right for a polymorphic association: `belongs_to :owner, polymorphic: true` backed by
  `index_accounts_on_owner (owner_type, owner_id)` — a composite index on both columns,
  not just one. Use that as the reference shape for any new polymorphic association.
- **A `uniqueness: true` validation needs a matching unique DB index.** The Rails
  validation alone has a race condition (two requests can both pass the check before
  either inserts) — without `add_index :table, :column, unique: true`, it's not actually
  enforced.
- **A `null: false` presence expectation needs the DB column to actually be
  `null: false`.** A model-level `validates :x, presence: true` without the matching
  migration constraint only protects writes that go through that model — a console
  session, a raw SQL script, or a different code path can still insert a null.

### Associations

- Check `dependent:` on `has_many`/`has_one` where an orphaned child row would be a
  correctness or storage problem — a missing `dependent: :destroy`/`:nullify` isn't
  always wrong (sometimes orphaning is intended), but it should be a deliberate choice
  visible in the diff, not an oversight.
- `annotaterb` keeps the `== Schema Information` comment in sync on models and factories
  automatically (see `rspec-developer` for the mechanics) — a migration whose model
  annotation wasn't regenerated is a sign the change wasn't run through
  `bin/rails db:migrate` locally before committing.

### N+1 queries

No automatic detector is installed (no `bullet` gem) — this has to be caught by reading
the diff: a serializer or view iterating a collection and calling an association inside
the loop without `includes`/`preload` on the original query is the pattern to look for.
Flagging it is in scope; adding the `bullet` gem is a separate, larger decision — note it
as a suggestion in the report, don't silently add a new dependency as part of a review.

## Fix mode

Same loop as `rails-code-reviewer`'s Fix mode, against `docs/reports/database-review/`
reports — a fix here almost always means writing a new migration, never editing
`schema.rb` or an old migration file by hand. Never commits.
