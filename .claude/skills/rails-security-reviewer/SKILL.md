---
name: rails-security-reviewer
description: >-
  Security review for pis-gogrow — hand-rolled cookie auth, Google OmniAuth, strong
  params, secrets in ENV/Rails credentials. TRIGGER when a change touches
  authentication, authorization (skip_before_action :authenticate), external input,
  OmniAuth callbacks, or anything reading a secret. Also TRIGGERS to work through an
  existing dated SECURITY_REVIEW_FINDINGS report — see Fix mode.
---

Adapted from `security-reviewer` in the reference project. This repo already runs
Brakeman + bundler-audit + npm audit in `bin/ci` — this skill's job is to **triage those
findings and check what static analysis structurally can't** (auth bypass logic, OAuth
account-linking, secret handling conventions), not to re-implement scanning.

## Review mode

Scope and report location/format: same as `rails-code-reviewer` — diff against branch
base plus uncommitted changes, findings at
`padre-testing-gogrow/docs/reports/security-review/SECURITY_REVIEW_FINDINGS_<date>.md`.

### Run the existing scanners first, triage what they surface

```bash
bin/brakeman --quiet --no-pager
bin/bundler-audit
npm audit
```
Don't re-derive what these already catch (known-CVE gems, common Rails vuln patterns) —
spend review effort on what they structurally can't see.

### Auth — this app authenticates every request by default

`ApplicationController` authenticates from a signed `session_token` cookie on every
request; a controller opts out with `skip_before_action :authenticate`. **Any new or
changed `skip_before_action :authenticate` is a finding to justify, not wave through** —
confirm the action is genuinely meant to be public (e.g. the OmniAuth callback, the
sign-in page) and doesn't leak data that should require a session.

On validation failure, controllers redirect back with
`inertia: { errors: @record.errors }` (PRG) — check a failed action doesn't also render
data that should have required success first.

### OmniAuth (Google Sign-In)

`omniauth-google-oauth2` + `omniauth-rails_csrf_protection` are in the Gemfile — check
the callback handler doesn't **auto-link an OmniAuth-provided email to an existing local
account without verifying the app already trusts that email for that user**. This is a
known general risk with email-based OmniAuth account linking (an attacker who controls
an OAuth-verified email matching an existing account's email could otherwise take over
that account) — verify `spec/requests/omniauth_callbacks_spec.rb`-style coverage exists
for whatever linking logic is actually there; this skill doesn't assert the current
callback code has this bug, only that it's the specific thing to check.

### Strong params / mass assignment

Every controller `create`/`update` must build the record from
`params.require(...).permit(...)`, never raw `params[:model]` or `params.permit!`. A
newly added attribute on a model that isn't added to the corresponding `permit` list is
usually a bug, not a security hole — but a `permit!` or a `permit` list wider than the
form actually sends is the security finding.

### Secrets

Real secrets live in `config/credentials.yml.enc` (via `config/master.key`, never
committed) or `ENV` (`.env`, loaded by `dotenv-rails` in dev/test only — `.env` itself
must never be committed; `.env.example` must only ever contain placeholders, never a
real value, even temporarily). A hardcoded API key, token, or password literal anywhere
in `app/`, `config/`, or `lib/` — instead of `Rails.application.credentials.x` or
`ENV.fetch("X")` — is a finding regardless of whether it's also in `.gitignore`.

### SQL injection

`where("column = '#{value}'")` or any string-interpolated SQL is a finding regardless of
where the interpolated value comes from — use `where(column: value)` or a `?`/named
placeholder. `annotaterb`'s generated schema comments are read-only documentation, not a
place this applies.

### XSS

React escapes by default — a `dangerouslySetInnerHTML` anywhere in `app/javascript/` is
a finding unless the content is verifiably sanitized server-side first (and that
sanitization step should be visible in the same diff, not asserted from memory).

## Fix mode

Same loop as `rails-code-reviewer`'s Fix mode, against
`docs/reports/security-review/` reports. Never commits.
