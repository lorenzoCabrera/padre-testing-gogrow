---
name: capybara-smoke-check
description: >-
  Ad-hoc, disposable verification that a just-built feature actually works end to end in
  pis-gogrow — a throwaway RSpec system spec run once and deleted, not committed
  coverage. TRIGGER after implementing a feature/fix, before calling it done, when you
  want real browser proof rather than trusting request specs alone. For committed
  regression coverage of the same flow, use capybara-system-suite instead.
---

Adapted from `e2e-testing` in the reference project — same posture (fast, local, thrown
away after use) minus the multi-service startup that project needed (Postgres/Mongo/
Redis/Kafka via loose `docker run`). Here it's just the Rails+Vite dev stack.

## When to reach for this vs. `capybara-system-suite`

- Just finished a feature and want to see it actually work through a real login and a
  real browser before considering it done → this skill.
- Want that same flow to keep being checked on every future change → write it as a
  committed spec under `spec/system/` instead (`capybara-system-suite`), don't leave a
  scratch file lying around pretending to be regression coverage.

## Prerequisites

```bash
cd pis-gogrow
bin/setup      # first time only
bin/dev        # rails + vite, if not already running
```

If `spec/support/capybara.rb` doesn't exist yet, set it up first per
`capybara-system-suite`'s "First-time setup" — both skills need the same driver config.

## The check

Write one throwaway spec, run it, then delete it — it never gets committed:

```ruby
# frozen_string_literal: true
# spec/system/zz_scratch_check_spec.rb — delete after use, not committed

RSpec.describe "Scratch check" do
  it "does the thing I just built" do
    sign_in(users(:one))
    visit menus_path
    # ... the actual flow being verified
    expect(page).to have_content("expected result")
  end
end
```

The `zz_scratch_` prefix is a hygiene convention, not a technical constraint — RSpec
loads anything under `spec/` matching `_spec.rb`, unlike a test runner with a strict
file-pattern allowlist. It exists so the file is unmistakably "delete me" if you forget,
and sorts to the bottom of any directory listing.

```bash
bin/rspec spec/system/zz_scratch_check_spec.rb
rm spec/system/zz_scratch_check_spec.rb   # always, once it passes
```

## What this catches that request specs don't

Request specs (`rspec-developer`) verify the Rails response — component name, props,
status. They don't catch a React-side bug: a prop the frontend reads under the wrong
key, a form that doesn't actually submit, a client-side validation blocking a valid
input. A real browser run is the only one of these three that would have caught that.
