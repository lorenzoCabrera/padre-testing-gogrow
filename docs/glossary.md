# Glossary

**Inertia.js** — server-driven SPA glue. Rails owns routing/data/auth;
React only renders. No client-side router, no client-side data fetching.

**Alba / `alba-inertia`** — the serialization layer this app actually uses
instead of plain `inertia_rails`. Controllers inherit `InertiaController`;
`default_render` is overridden so instance variables become Inertia props
via a matching `*Serializer` class, instead of an explicit
`render inertia: { key: value }` call. This is the opposite of what the
generic `inertia_rails` docs (and the vendored `inertia-rails-architecture`
skill) describe — `pis-gogrow/AGENTS.md` is explicit that `alba-inertia`
wins wherever the two disagree.

**Typelizer** — generates the two checked-in TS trees
(`app/javascript/types/serializers/`, `app/javascript/routes/`) from Ruby
serializers/routes. Never hand-edited; CI fails if they drift from
`bin/rails typelizer:generate:refresh`.

**SSR** — server-side rendering of the React app, served by an
`:inertia_ssr` Puma plugin (`config/initializers/inertia_rails.rb`).

**solid_cache / solid_queue / solid_cable** — Rails 8's database-backed
adapters (replacing Redis-backed Sidekiq/ActionCable setups) for caching,
background jobs, and Action Cable, all on the primary Postgres database.

**Kamal** — the deploy tool this app ships with (Docker-based, no k8s).

**`skills-lock.json`** — tracks the vendored `inertia-rails/skills` set's
source and content hash inside `pis-gogrow/.claude/skills/`. Unrelated to
anything in this repo; don't edit it.
